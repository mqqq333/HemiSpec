from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import pandas as pd

from .compute import compute_ans_rns_arrays, run_compute as _run_compute
from .dgn_inference import run_dgn_inference_files
from .dgn_model import load_generator, resolve_device
from .hemisphere_classifier import run_hemisphere_classifier
from .paths import (
    default_classifier_output_path,
    default_input_glob,
    default_trt_output_path,
    resolve_classifier_model_dir,
    resolve_dgn_model_root,
    resolve_glasser_atlas_path,
    resolve_glasser_label_table,
    resolve_preprocess_script,
    resolve_sample_input_dir,
)
from .plots import plot_heatmap, plot_within_between_box
from .reports import save_specificity_result
from .roi import RoiSummaryConfig, summarize_maps_by_atlas
from .similarity import (
    DEFAULT_HEMI_SLICES,
    SpecificityResult,
    compute_specificity,
    paired_paths_for_sessions,
    parse_hemi_slices,
)


PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_PREPROCESS_SCRIPT = resolve_preprocess_script()
DEFAULT_DGN_CHECKPOINTS = {
    "R_to_L": ("best_netG_R2L.pth", "netG_R2L.pth", "best_netG_L.pth", "netG_L.pth"),
    "L_to_R": ("best_netG_L2R.pth", "netG_L2R.pth", "best_netG_R.pth", "netG_R.pth"),
}


@dataclass(frozen=True)
class PreprocessingSpec:
    """Document the expected GM preprocessing contract for public callers."""

    script_path: Path = DEFAULT_PREPROCESS_SCRIPT
    sample_input_dir: Path | None = None
    input_description: str = "T1-weighted NIfTI image"
    output_suffix: str = "_GM_masked.nii.gz"
    reference_image: str = "MNI152_T1_1.5mm_brain.nii.gz"
    gm_threshold: float = 0.15
    requires_fsl: bool = True


@dataclass(frozen=True)
class DGNModelBundle:
    """Metadata for a deployed trained DGN model bundle.

    This public contract describes runtime inference assets only. Training code
    can be used as methodological reference during development, but it is not a
    product dependency and is intentionally not exposed here.
    """

    checkpoint: Path
    config: Path | None = None
    output_dir: Path | None = None
    direction: Literal["L_to_R", "R_to_L"] | None = None
    source_hemisphere: Literal["left", "right"] | None = None
    target_hemisphere: Literal["left", "right"] | None = None
    name: str = "DGN"
    version: str | None = None


@dataclass(frozen=True)
class DGNInferenceConfig:
    model: DGNModelBundle
    input_glob: str
    out_dir: Path
    device: Literal["auto", "cpu", "cuda"] = "auto"
    batch_size: int = 1
    direction: Literal["both", "L_to_R", "R_to_L"] = "both"
    clip_recon: tuple[float, float] | None = None
    output_suffix: str = "_PRED_LR_full.nii.gz"


@dataclass(frozen=True)
class MetricComputeConfig:
    actual_glob: str
    reconstructed_glob: str
    out_dir: Path
    gm_thresh: float = 0.15
    eps: float = 1e-6
    reconstructed_suffix_to_strip: str = "_PRED_LR_full"
    actual_suffix_to_strip: str = ""
    clip_recon: tuple[float, float] | None = None
    export_voxelwise: bool = True
    save_subject_maps: bool = False
    write_nan_outside: bool = False
    verbose_every: int = 50
    roi_atlas: Path | None = None
    roi_out_csv: Path | None = None
    roi_label_table: Path | None = None
    roi_stat: Literal["mean", "median"] = "mean"
    roi_ignore_zero: bool = True


@dataclass(frozen=True)
class MetricComputeResult:
    n_actual: int
    n_reconstructed: int
    n_pairs: int
    missing_actual: list[str]
    missing_reconstructed: list[str]
    out_dir: Path
    subject_maps_dir: Path | None = None
    roi_csv: Path | None = None
    group_maps_saved: bool = True

    @classmethod
    def from_legacy_dict(cls, value: dict[str, object]) -> "MetricComputeResult":
        subject_maps_dir = value.get("subject_maps_dir")
        roi_csv = value.get("roi_csv")
        return cls(
            n_actual=int(value["n_actual"]),
            n_reconstructed=int(value["n_predicted"]),
            n_pairs=int(value["n_pairs"]),
            missing_actual=list(value["missing_actual"]),
            missing_reconstructed=list(value["missing_predicted"]),
            out_dir=Path(str(value["out_dir"])),
            subject_maps_dir=Path(str(subject_maps_dir)) if subject_maps_dir else None,
            roi_csv=Path(str(roi_csv)) if roi_csv else None,
            group_maps_saved=bool(value.get("group_maps_saved", True)),
        )


@dataclass(frozen=True)
class PipelineRunConfig:
    """End-to-end trained DGN inference followed by ANS/RNS metric computation."""

    inference: DGNInferenceConfig
    metrics_out_dir: Path
    gm_thresh: float = 0.15
    eps: float = 1e-6
    reconstructed_suffix_to_strip: str = "_PRED_LR_full"
    actual_suffix_to_strip: str = ""
    save_subject_maps: bool = True
    write_nan_outside: bool = False
    verbose_every: int = 50
    export_voxelwise: bool = True
    roi_atlas: Path | None = None
    roi_out_csv: Path | None = None
    roi_label_table: Path | None = None
    roi_stat: Literal["mean", "median"] = "mean"
    roi_ignore_zero: bool = True


@dataclass(frozen=True)
class PipelineRunResult:
    reconstructed_paths: list[Path]
    metrics: MetricComputeResult


@dataclass(frozen=True)
class ValidationConfig:
    maps_dir: Path
    out_dir: Path
    kinds: tuple[str, ...] = ("ANS", "RNS")
    suffix_template: str = "_{kind}.nii.gz"
    file_regex: str = r"(sub-MSC\d+).*?(run-\d+)"
    session_a: str = "run-01"
    session_b: str = "run-02"
    hemis: tuple[str, ...] = ("L", "R")
    dgn_direction: Literal["auto", "L_to_R", "R_to_L", "bilateral"] | None = None
    hemi_slices: str | None = None
    metric: Literal["pearson", "spearman"] = "pearson"
    mask_type: Literal["rate", "max"] = "rate"
    thr: float = 0.0
    rate_thr: float = 0.3
    mask_mode: Literal["union", "intersect"] = "union"
    symmetrize: bool = True
    write_plots: bool = True


@dataclass(frozen=True)
class ValidationSummaryRow:
    kind: str
    hemi: str
    n_subjects: int
    n_voxels: int
    match_rate: float
    specificity_index: float
    cohen_d: float
    within_mean: float
    between_mean: float
    t_value: float
    p_value: float

    def as_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "hemi": self.hemi,
            "n_subjects": self.n_subjects,
            "n_voxels": self.n_voxels,
            "match_rate": self.match_rate,
            "specificity_index": self.specificity_index,
            "cohen_d": self.cohen_d,
            "within_mean": self.within_mean,
            "between_mean": self.between_mean,
            "t_value": self.t_value,
            "p_value": self.p_value,
        }


@dataclass(frozen=True)
class ValidationRunResult:
    results: list[SpecificityResult] = field(default_factory=list)
    summary_rows: list[ValidationSummaryRow] = field(default_factory=list)
    summary_csv: Path | None = None
    out_dir: Path | None = None

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([row.as_dict() for row in self.summary_rows])


@dataclass(frozen=True)
class HemisphereClassificationConfig:
    """Config for ROI-level hemisphere-classifier validation."""

    maps_dir: Path
    roi_csv: Path | None = None
    atlas_path: Path | None = None
    label_table: Path | None = None
    classifier_checkpoint: Path | None = None
    classifier_model_dir: Path | None = None
    classifier_mode: Literal["single", "paired_residual"] = "single"
    out_dir: Path | None = None
    kinds: tuple[str, ...] = ("ANS", "RNS")
    suffix_template: str = "_{kind}.nii.gz"
    file_regex: str = r"(?P<subject>.+?)_{kind}\.nii(?:\.gz)?$"
    roi_ignore_zero: bool = True
    device: Literal["auto", "cpu", "cuda"] = "auto"
    batch_size: int = 1


@dataclass(frozen=True)
class HemisphereClassificationResult:
    accuracy: float | None = None
    n_samples: int = 0
    summary_csv: Path | None = None
    predictions_csv: Path | None = None
    out_dir: Path | None = None
    message: str = ""


def get_preprocessing_spec(project_root: str | Path | None = None) -> PreprocessingSpec:
    return PreprocessingSpec(
        script_path=resolve_preprocess_script(project_root),
        sample_input_dir=resolve_sample_input_dir(project_root),
    )


def discover_local_dgn_bundles(root: str | Path | None = None) -> dict[str, DGNModelBundle]:
    root = resolve_dgn_model_root(root)
    specs = {
        "R_to_L": {
            "output_dir": root / "outputs_bi_stable_L",
            "checkpoint_names": DEFAULT_DGN_CHECKPOINTS["R_to_L"],
            "source_hemisphere": "right",
            "target_hemisphere": "left",
            "name": "outputs_bi_stable_L",
        },
        "L_to_R": {
            "output_dir": root / "outputs_bi_stable_R",
            "checkpoint_names": DEFAULT_DGN_CHECKPOINTS["L_to_R"],
            "source_hemisphere": "left",
            "target_hemisphere": "right",
            "name": "outputs_bi_stable_R",
        },
    }

    bundles: dict[str, DGNModelBundle] = {}
    for direction, spec in specs.items():
        output_dir = Path(spec["output_dir"])
        ckpt_dir = output_dir / "ckpts"
        checkpoint = _first_existing(ckpt_dir / name for name in spec["checkpoint_names"])
        if checkpoint is None:
            continue
        bundles[direction] = DGNModelBundle(
            checkpoint=checkpoint,
            output_dir=output_dir,
            direction=direction,  # type: ignore[arg-type]
            source_hemisphere=spec["source_hemisphere"],  # type: ignore[arg-type]
            target_hemisphere=spec["target_hemisphere"],  # type: ignore[arg-type]
            name=spec["name"],
        )
    return bundles


def run_dgn_inference(config: DGNInferenceConfig) -> list[Path]:
    direction = _resolve_inference_direction(config)
    device = resolve_device(config.device)
    model = load_generator(config.model.checkpoint, device=device)
    outputs = run_dgn_inference_files(
        input_glob=config.input_glob,
        out_dir=config.out_dir,
        model=model,
        direction=direction,
        device=device,
        output_suffix=config.output_suffix,
        clip_recon=config.clip_recon,
    )
    return [item.output_path for item in outputs]


def compute_metrics(config: MetricComputeConfig) -> MetricComputeResult:
    save_subject_maps = config.save_subject_maps or config.roi_atlas is not None
    result = _run_compute(
        actual_glob=config.actual_glob,
        predicted_glob=config.reconstructed_glob,
        out_dir=config.out_dir,
        gm_thresh=config.gm_thresh,
        eps=config.eps,
        pred_suffix_to_strip=config.reconstructed_suffix_to_strip,
        actual_suffix_to_strip=config.actual_suffix_to_strip,
        clip_recon=config.clip_recon,
        save_subject_maps=save_subject_maps,
        save_group_maps=config.export_voxelwise,
        write_nan_outside=config.write_nan_outside,
        verbose_every=config.verbose_every,
    )
    subject_maps_dir = result.get("subject_maps_dir")
    if config.roi_atlas is not None:
        if not subject_maps_dir:
            raise RuntimeError("ROI-wise export requires subject-level ANS/RNS maps.")
        roi_csv = config.roi_out_csv or (Path(config.out_dir) / "roi_summary.csv")
        summarize_maps_by_atlas(
            RoiSummaryConfig(
                maps_glob=str(Path(str(subject_maps_dir)) / "*.nii.gz"),
                atlas_path=config.roi_atlas,
                out_csv=roi_csv,
                label_table=config.roi_label_table,
                stat=config.roi_stat,
                ignore_zero=config.roi_ignore_zero,
            )
        )
        result["roi_csv"] = str(roi_csv)
    return MetricComputeResult.from_legacy_dict(result)


def run_pipeline(config: PipelineRunConfig) -> PipelineRunResult:
    reconstructed_paths = run_dgn_inference(config.inference)
    metrics = compute_metrics(
        MetricComputeConfig(
            actual_glob=config.inference.input_glob,
            reconstructed_glob=str(Path(config.inference.out_dir) / f"*{config.inference.output_suffix}"),
            out_dir=config.metrics_out_dir,
            gm_thresh=config.gm_thresh,
            eps=config.eps,
            reconstructed_suffix_to_strip=config.reconstructed_suffix_to_strip,
            actual_suffix_to_strip=config.actual_suffix_to_strip,
            clip_recon=config.inference.clip_recon,
            export_voxelwise=config.export_voxelwise,
            save_subject_maps=config.save_subject_maps,
            write_nan_outside=config.write_nan_outside,
            verbose_every=config.verbose_every,
            roi_atlas=config.roi_atlas,
            roi_out_csv=config.roi_out_csv,
            roi_label_table=config.roi_label_table,
            roi_stat=config.roi_stat,
            roi_ignore_zero=config.roi_ignore_zero,
        )
    )
    return PipelineRunResult(reconstructed_paths=reconstructed_paths, metrics=metrics)


def validate_specificity(config: ValidationConfig) -> ValidationRunResult:
    out = Path(config.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    hemi_slices = parse_hemi_slices(config.hemi_slices)
    hemis = resolve_validation_hemis(config.hemis, config.dgn_direction, config.maps_dir)
    results: list[SpecificityResult] = []
    rows: list[ValidationSummaryRow] = []

    for kind in _normalize_labels(config.kinds):
        subjects, scan_a, scan_b = paired_paths_for_sessions(
            config.maps_dir,
            kind=kind,
            session_a=config.session_a,
            session_b=config.session_b,
            suffix_template=config.suffix_template,
            file_regex=config.file_regex,
        )
        if not subjects:
            raise RuntimeError(
                f"No subjects with both {config.session_a} and {config.session_b} for {kind}. "
                "Check maps_dir, file_regex and suffix_template."
            )

        for hemi in hemis:
            result = compute_specificity(
                scan_a,
                scan_b,
                subjects=subjects,
                kind=kind,
                hemi=hemi,
                metric=config.metric,
                mask_type=config.mask_type,
                thr=config.thr,
                rate_thr=config.rate_thr,
                mask_mode=config.mask_mode,
                hemi_slices=hemi_slices,
                symmetrize=config.symmetrize,
            )
            label = f"{kind}_{hemi}"
            save_specificity_result(result, out, label)
            if config.write_plots:
                plot_heatmap(result.matrix, out / f"heatmap_{label}.png", f"{kind}.{hemi} MR={result.match_rate:.0f}%")
                plot_within_between_box(result.within, result.between, out / f"boxplot_{label}.png", f"{kind}.{hemi}")

            results.append(result)
            rows.append(
                ValidationSummaryRow(
                    kind=kind,
                    hemi=hemi,
                    n_subjects=len(subjects),
                    n_voxels=result.n_voxels,
                    match_rate=result.match_rate,
                    specificity_index=result.specificity_index,
                    cohen_d=result.cohen_d,
                    within_mean=float(result.within.mean()),
                    between_mean=float(result.between.mean()),
                    t_value=result.t_value,
                    p_value=result.p_value,
                )
            )

    summary_csv = out / "validation_summary.csv"
    pd.DataFrame([row.as_dict() for row in rows]).to_csv(summary_csv, index=False)
    return ValidationRunResult(results=results, summary_rows=rows, summary_csv=summary_csv, out_dir=out)


def validate_reliability(config: ValidationConfig) -> ValidationRunResult:
    return validate_specificity(config)


def validate_hemisphere_classification(
    config: HemisphereClassificationConfig,
) -> HemisphereClassificationResult:
    """Run trained ROI-level hemisphere classifier validation.

    The deployed classifier was trained outside the toolkit on noICBM ROI
    features and evaluated on held-out ICBM subjects. This function loads the
    saved sklearn/joblib runtime and applies it to an ROI-wise ANS/RNS CSV.
    Training remains out of HemiSpec runtime scope.
    """

    model_path = config.classifier_checkpoint or resolve_classifier_model_dir(
        config.classifier_model_dir,
        mode=config.classifier_mode,
    )
    if model_path is None:
        raise ValueError("Provide classifier_checkpoint or classifier_model_dir.")
    if config.roi_csv is None:
        if config.atlas_path is None:
            raise ValueError("Provide roi_csv, or provide atlas_path so ROI features can be generated from maps_dir.")
        out_dir = config.out_dir or (config.maps_dir / "hemisphere_classifier")
        roi_csv = out_dir / "roi_summary_for_classifier.csv"
        summarize_maps_by_atlas(
            RoiSummaryConfig(
                maps_glob=str(config.maps_dir / "*.nii.gz"),
                atlas_path=config.atlas_path,
                out_csv=roi_csv,
                label_table=config.label_table,
                ignore_zero=config.roi_ignore_zero,
            )
        )
    else:
        roi_csv = config.roi_csv

    run = run_hemisphere_classifier(
        roi_csv=roi_csv,
        model_path=model_path,
        out_dir=config.out_dir,
        metrics=config.kinds,
    )
    accuracy = float(run.summary["accuracy"].mean()) if "accuracy" in run.summary and not run.summary.empty else None
    return HemisphereClassificationResult(
        accuracy=accuracy,
        n_samples=int(run.summary["n_samples"].sum()) if "n_samples" in run.summary and not run.summary.empty else 0,
        summary_csv=run.summary_csv,
        predictions_csv=run.predictions_csv,
        out_dir=config.out_dir,
        message=run.message,
    )


def _normalize_labels(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(value.strip().upper() for value in values if value.strip())


def normalize_dgn_direction(direction: str | None) -> Literal["auto", "L_to_R", "R_to_L", "bilateral"] | None:
    if direction is None:
        return None
    value = direction.strip().replace("-", "_").upper()
    if value in {"", "AUTO"}:
        return "auto"
    if value in {"L_TO_R", "L2R", "LEFT_TO_RIGHT"}:
        return "L_to_R"
    if value in {"R_TO_L", "R2L", "RIGHT_TO_LEFT"}:
        return "R_to_L"
    if value in {"BILATERAL", "BOTH", "L_R", "R_L"}:
        return "bilateral"
    raise ValueError("dgn_direction must be one of: auto, L_to_R, R_to_L, bilateral")


def target_hemisphere_for_direction(direction: str | None) -> str | None:
    normalized = normalize_dgn_direction(direction)
    if normalized == "L_to_R":
        return "R"
    if normalized == "R_to_L":
        return "L"
    return None


def infer_dgn_direction_from_path(path: str | Path | None) -> Literal["L_to_R", "R_to_L"] | None:
    if path is None:
        return None
    text = str(path).replace("-", "_").lower()
    has_l_to_r = "l_to_r" in text or "l2r" in text
    has_r_to_l = "r_to_l" in text or "r2l" in text
    if has_l_to_r and not has_r_to_l:
        return "L_to_R"
    if has_r_to_l and not has_l_to_r:
        return "R_to_L"
    return None


def resolve_validation_hemis(
    hemis: tuple[str, ...] = ("L", "R"),
    dgn_direction: str | None = None,
    maps_dir: str | Path | None = None,
) -> tuple[str, ...]:
    labels = _normalize_labels(hemis)
    if not labels:
        labels = ("AUTO",)

    auto_labels = {"AUTO", "TARGET"}
    if any(label in auto_labels for label in labels):
        if len(labels) > 1:
            raise ValueError("Use a single --hemis auto/target value, or pass explicit hemispheres such as L,R.")
        requested_target = labels[0] == "TARGET"
        normalized_direction = normalize_dgn_direction(dgn_direction)
        inferred_direction = None if normalized_direction not in (None, "auto") else infer_dgn_direction_from_path(maps_dir)
        direction = inferred_direction or (normalized_direction if normalized_direction != "auto" else None)
        target = target_hemisphere_for_direction(direction)
        if target:
            return (target,)
        if requested_target:
            raise ValueError("hemis=target requires --dgn-direction L_to_R/R_to_L or a maps_dir path containing that direction.")
        return ("L", "R")

    return labels


def _resolve_inference_direction(config: DGNInferenceConfig) -> str:
    if config.direction != "both":
        return config.direction
    if config.model.direction is None:
        raise ValueError("DGNInferenceConfig.direction='both' requires model.direction to be set.")
    return config.model.direction


def _first_existing(paths) -> Path | None:
    for path in paths:
        path = Path(path)
        if path.exists():
            return path
    return None


__all__ = [
    "DEFAULT_HEMI_SLICES",
    "DGNInferenceConfig",
    "DGNModelBundle",
    "HemisphereClassificationConfig",
    "HemisphereClassificationResult",
    "MetricComputeConfig",
    "MetricComputeResult",
    "PipelineRunConfig",
    "PipelineRunResult",
    "PreprocessingSpec",
    "SpecificityResult",
    "ValidationConfig",
    "ValidationRunResult",
    "ValidationSummaryRow",
    "compute_ans_rns_arrays",
    "compute_metrics",
    "default_classifier_output_path",
    "default_input_glob",
    "default_trt_output_path",
    "discover_local_dgn_bundles",
    "get_preprocessing_spec",
    "infer_dgn_direction_from_path",
    "normalize_dgn_direction",
    "resolve_validation_hemis",
    "resolve_classifier_model_dir",
    "resolve_dgn_model_root",
    "resolve_glasser_atlas_path",
    "resolve_glasser_label_table",
    "run_dgn_inference",
    "run_pipeline",
    "target_hemisphere_for_direction",
    "validate_reliability",
    "validate_hemisphere_classification",
    "validate_specificity",
]
