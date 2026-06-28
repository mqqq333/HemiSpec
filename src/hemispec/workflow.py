from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd

from .api import (
    DGNInferenceConfig,
    HemisphereClassificationConfig,
    HemisphereClassificationResult,
    MetricComputeConfig,
    MetricComputeResult,
    PipelineRunConfig,
    PipelineRunResult,
    ValidationConfig,
    ValidationRunResult,
    compute_metrics,
    discover_local_dgn_bundles,
    run_pipeline,
    validate_hemisphere_classification,
    validate_reliability,
)
from .dgn_inference import LEFT_SLICE, RIGHT_SLICE
from .io import list_from_glob, load_nifti, save_like, strip_nii_ext
from .paths import resolve_classifier_model_dir, resolve_glasser_atlas_path, resolve_glasser_label_table
from .roi import RoiSummaryConfig, summarize_maps_by_atlas


@dataclass(frozen=True)
class BilateralWorkflowConfig:
    """One-entry deployed workflow for bilateral DGN, ANS/RNS export, and validation."""

    input_glob: str
    out_dir: Path
    model_root: Path | None = None
    device: str = "auto"
    gm_thresh: float = 0.15
    eps: float = 1e-6
    clip_recon: tuple[float, float] | None = None
    output_suffix: str = "_PRED_LR_full.nii.gz"
    reconstructed_suffix_to_strip: str = "_PRED_LR_full"
    actual_suffix_to_strip: str = ""
    export_voxelwise: bool = True
    write_nan_outside: bool = True
    export_roi_table: bool = True
    roi_atlas: Path | None = None
    roi_label_table: Path | None = None
    roi_stat: str = "mean"
    roi_ignore_zero: bool = True
    run_classifier: bool = False
    classifier_model_dir: Path | None = None
    classifier_mode: str = "single"
    classifier_out_dir: Path | None = None
    run_trt: bool = False
    trt_file_regex: str = r"(sub-MSC\d+).*?(run-\d+)"
    trt_session_a: str = "run-01"
    trt_session_b: str = "run-02"
    trt_metric: str = "pearson"
    trt_mask_type: str = "rate"
    trt_thr: float = 0.0
    trt_rate_thr: float = 0.3
    trt_mask_mode: str = "union"
    trt_symmetrize: bool = True
    trt_write_plots: bool = True
    verbose_every: int = 50


@dataclass(frozen=True)
class BilateralWorkflowResult:
    out_dir: Path
    l_to_r: PipelineRunResult
    r_to_l: PipelineRunResult
    combined_maps_dir: Path
    hemi_maps_dir: Path
    roi_csv: Path | None
    roi_wide_csv: Path | None
    subject_summary_csv: Path
    classifier: HemisphereClassificationResult | None = None
    trt: ValidationRunResult | None = None


def run_bilateral_workflow(config: BilateralWorkflowConfig) -> BilateralWorkflowResult:
    out = Path(config.out_dir)
    recon_dir = out / "recon"
    metrics_dir = out / "metrics"
    combined_dir = out / "subject_maps"
    hemi_dir = out / "subject_hemi_maps"
    tables_dir = out / "tables"
    for directory in (recon_dir, metrics_dir, combined_dir, hemi_dir, tables_dir):
        directory.mkdir(parents=True, exist_ok=True)

    roi_atlas = _resolve_optional_roi_atlas(config)
    roi_label_table = _resolve_optional_roi_label_table(config) if roi_atlas is not None else None
    bundles = discover_local_dgn_bundles(config.model_root)
    missing = [direction for direction in ("L_to_R", "R_to_L") if direction not in bundles]
    if missing:
        raise RuntimeError(f"Missing configured local DGN direction(s): {', '.join(missing)}")

    l_to_r = _run_one_direction(config, bundles["L_to_R"], "L_to_R", recon_dir, metrics_dir, roi_atlas, roi_label_table)
    r_to_l = _run_one_direction(config, bundles["R_to_L"], "R_to_L", recon_dir, metrics_dir, roi_atlas, roi_label_table)

    _write_bilateral_subject_maps(
        l_to_r.metrics.subject_maps_dir,
        r_to_l.metrics.subject_maps_dir,
        combined_dir,
        hemi_dir,
        write_nan_outside=config.write_nan_outside,
    )
    roi_csv: Path | None = None
    roi_wide_csv: Path | None = None
    if roi_atlas is not None:
        roi_csv = tables_dir / "roi_features_bilateral.csv"
        roi_wide_csv = tables_dir / "roi_features_bilateral_wide.csv"
        summarize_maps_by_atlas(
            RoiSummaryConfig(
                maps_glob=str(combined_dir / "*.nii.gz"),
                atlas_path=roi_atlas,
                out_csv=roi_csv,
                label_table=roi_label_table,
                stat=config.roi_stat,
                ignore_zero=config.roi_ignore_zero,
            )
        )
        summarize_bilateral_roi_features(roi_csv, roi_wide_csv)
    subject_summary_csv = tables_dir / "subject_metric_summary.csv"
    summarize_subject_metrics(combined_dir, subject_summary_csv)

    classifier_result = None
    if config.run_classifier:
        if roi_csv is None or roi_atlas is None:
            raise RuntimeError(
                "Hemisphere classifier validation requires ROI table export. "
                "Provide an ROI atlas, keep export_roi_table enabled, or disable run_classifier."
            )
        classifier_result = validate_hemisphere_classification(
            HemisphereClassificationConfig(
                maps_dir=combined_dir,
                roi_csv=roi_csv,
                atlas_path=roi_atlas,
                label_table=roi_label_table,
                classifier_model_dir=resolve_classifier_model_dir(config.classifier_model_dir, mode=config.classifier_mode),
                classifier_mode=config.classifier_mode,  # type: ignore[arg-type]
                out_dir=config.classifier_out_dir or (out / "hemisphere_classifier"),
            )
        )

    trt_result = None
    if config.run_trt:
        trt_result = validate_reliability(
            ValidationConfig(
                maps_dir=combined_dir,
                out_dir=out / "trt",
                kinds=("ANS", "RNS"),
                file_regex=config.trt_file_regex,
                session_a=config.trt_session_a,
                session_b=config.trt_session_b,
                hemis=("L", "R"),
                dgn_direction="bilateral",
                metric=config.trt_metric,  # type: ignore[arg-type]
                mask_type=config.trt_mask_type,  # type: ignore[arg-type]
                thr=config.trt_thr,
                rate_thr=config.trt_rate_thr,
                mask_mode=config.trt_mask_mode,  # type: ignore[arg-type]
                symmetrize=config.trt_symmetrize,
                write_plots=config.trt_write_plots,
            )
        )

    return BilateralWorkflowResult(
        out_dir=out,
        l_to_r=l_to_r,
        r_to_l=r_to_l,
        combined_maps_dir=combined_dir,
        hemi_maps_dir=hemi_dir,
        roi_csv=roi_csv,
        roi_wide_csv=roi_wide_csv,
        subject_summary_csv=subject_summary_csv,
        classifier=classifier_result,
        trt=trt_result,
    )


def _resolve_optional_roi_atlas(config: BilateralWorkflowConfig) -> Path | None:
    """Return an ROI atlas when ROI tables/classifier are requested and available.

    Voxel-wise ANS/RNS maps are the primary workflow output. Missing atlas assets
    should not block that primary output unless the user explicitly requests a
    downstream step that requires ROI features, such as classifier validation.
    """

    if not config.export_roi_table and not config.run_classifier:
        return None
    atlas = config.roi_atlas or resolve_glasser_atlas_path()
    if atlas.exists():
        return atlas
    if config.run_classifier:
        raise RuntimeError(f"Hemisphere classifier validation requires an existing ROI atlas: {atlas}")
    return None


def _resolve_optional_roi_label_table(config: BilateralWorkflowConfig) -> Path | None:
    label_table = config.roi_label_table or resolve_glasser_label_table()
    return label_table if label_table.exists() else None


def summarize_subject_metrics(maps_dir: Path, out_csv: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for ans_path in list_from_glob(str(maps_dir / "*_ANS.nii.gz")):
        subject = strip_nii_ext(ans_path.name)[: -len("_ANS")]
        rns_path = maps_dir / f"{subject}_RNS.nii.gz"
        if not rns_path.exists():
            continue
        ans = load_nifti(ans_path).data
        rns = load_nifti(rns_path).data
        rows.append(_summary_row(subject, ans, rns))
    df = pd.DataFrame(rows)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    return df


def summarize_bilateral_roi_features(roi_csv: Path, wide_csv: Path | None = None) -> pd.DataFrame:
    """Annotate ROI rows with explicit hemisphere metric names and optionally write a wide table."""

    df = pd.read_csv(roi_csv)
    if not {"subject", "kind", "roi_label", "value"}.issubset(df.columns):
        raise ValueError("Bilateral ROI CSV must contain subject, kind, roi_label, and value columns.")

    df["hemi"] = df["roi_label"].map(_roi_label_to_hemi)
    df["roi_index"] = df["roi_label"].map(_roi_label_to_compact_index)
    valid = df["hemi"].isin(["L", "R"]) & df["roi_index"].notna()
    df["metric_hemi"] = df["kind"].astype(str)
    df.loc[valid, "metric_hemi"] = df.loc[valid, "kind"].astype(str) + "." + df.loc[valid, "hemi"].astype(str)
    df["feature_name"] = ""
    df.loc[valid, "feature_name"] = (
        df.loc[valid, "metric_hemi"].astype(str)
        + "_roi_"
        + df.loc[valid, "roi_index"].astype(int).astype(str)
    )
    df.to_csv(roi_csv, index=False)

    if wide_csv is not None:
        wide = (
            df.loc[valid]
            .pivot_table(index="subject", columns="feature_name", values="value", aggfunc="mean")
            .reset_index()
        )
        wide.columns.name = None
        wide_csv.parent.mkdir(parents=True, exist_ok=True)
        wide.to_csv(wide_csv, index=False)

    return df


def _run_one_direction(
    config: BilateralWorkflowConfig,
    model,
    direction: str,
    recon_root: Path,
    metrics_root: Path,
    roi_atlas: Path | None,
    roi_label_table: Path | None,
) -> PipelineRunResult:
    return run_pipeline(
        PipelineRunConfig(
            inference=DGNInferenceConfig(
                model=model,
                input_glob=config.input_glob,
                out_dir=recon_root / direction,
                device=config.device,  # type: ignore[arg-type]
                direction=direction,  # type: ignore[arg-type]
                clip_recon=config.clip_recon,
                output_suffix=config.output_suffix,
            ),
            metrics_out_dir=metrics_root / direction,
            gm_thresh=config.gm_thresh,
            eps=config.eps,
            reconstructed_suffix_to_strip=config.reconstructed_suffix_to_strip,
            actual_suffix_to_strip=config.actual_suffix_to_strip,
            save_subject_maps=True,
            write_nan_outside=config.write_nan_outside,
            verbose_every=config.verbose_every,
            export_voxelwise=config.export_voxelwise,
            roi_atlas=roi_atlas,
            roi_out_csv=(metrics_root / direction / "roi_summary.csv") if roi_atlas is not None else None,
            roi_label_table=roi_label_table,
            roi_stat=config.roi_stat,  # type: ignore[arg-type]
            roi_ignore_zero=config.roi_ignore_zero,
        )
    )


def _write_bilateral_subject_maps(
    l_to_r_maps_dir: Path | None,
    r_to_l_maps_dir: Path | None,
    combined_dir: Path,
    hemi_dir: Path,
    write_nan_outside: bool = False,
) -> None:
    if l_to_r_maps_dir is None or r_to_l_maps_dir is None:
        raise RuntimeError("Bilateral workflow requires subject-level maps for both DGN directions.")

    l_to_r_ans = {strip_nii_ext(path.name)[: -len("_ANS")]: path for path in list_from_glob(str(l_to_r_maps_dir / "*_ANS.nii.gz"))}
    r_to_l_ans = {strip_nii_ext(path.name)[: -len("_ANS")]: path for path in list_from_glob(str(r_to_l_maps_dir / "*_ANS.nii.gz"))}
    subjects = sorted(set(l_to_r_ans).intersection(r_to_l_ans))
    if not subjects:
        raise RuntimeError("No paired L_to_R/R_to_L subject maps found for bilateral merge.")

    for subject in subjects:
        l_ans_path = l_to_r_maps_dir / f"{subject}_ANS.nii.gz"
        l_rns_path = l_to_r_maps_dir / f"{subject}_RNS.nii.gz"
        r_ans_path = r_to_l_maps_dir / f"{subject}_ANS.nii.gz"
        r_rns_path = r_to_l_maps_dir / f"{subject}_RNS.nii.gz"
        l_ref = load_nifti(l_ans_path)
        l_ans = l_ref.data
        l_rns = load_nifti(l_rns_path).data
        r_ans = load_nifti(r_ans_path).data
        r_rns = load_nifti(r_rns_path).data

        ans_l = _hemi_only(r_ans, "L", write_nan_outside)
        ans_r = _hemi_only(l_ans, "R", write_nan_outside)
        rns_l = _hemi_only(r_rns, "L", write_nan_outside)
        rns_r = _hemi_only(l_rns, "R", write_nan_outside)
        ans = _combine_lr(ans_l, ans_r, write_nan_outside)
        rns = _combine_lr(rns_l, rns_r, write_nan_outside)

        save_like(l_ref.image, ans_l, hemi_dir / f"{subject}_ANS.L.nii.gz")
        save_like(l_ref.image, ans_r, hemi_dir / f"{subject}_ANS.R.nii.gz")
        save_like(l_ref.image, rns_l, hemi_dir / f"{subject}_RNS.L.nii.gz")
        save_like(l_ref.image, rns_r, hemi_dir / f"{subject}_RNS.R.nii.gz")
        save_like(l_ref.image, ans, combined_dir / f"{subject}_ANS.nii.gz")
        save_like(l_ref.image, rns, combined_dir / f"{subject}_RNS.nii.gz")


def _hemi_only(data: np.ndarray, hemi: str, write_nan_outside: bool) -> np.ndarray:
    out = np.full(data.shape, np.nan, dtype=np.float32) if write_nan_outside else np.zeros(data.shape, dtype=np.float32)
    z, y, x = LEFT_SLICE if hemi == "L" else RIGHT_SLICE
    out[z, y, x] = data[z, y, x].astype(np.float32, copy=False)
    return out


def _combine_lr(left: np.ndarray, right: np.ndarray, write_nan_outside: bool) -> np.ndarray:
    out = np.full(left.shape, np.nan, dtype=np.float32) if write_nan_outside else np.zeros(left.shape, dtype=np.float32)
    lz, ly, lx = LEFT_SLICE
    rz, ry, rx = RIGHT_SLICE
    out[lz, ly, lx] = left[lz, ly, lx]
    out[rz, ry, rx] = right[rz, ry, rx]
    return out


def _summary_row(subject: str, ans: np.ndarray, rns: np.ndarray) -> dict[str, object]:
    return {
        "subject": subject,
        "ANS.L_mean": _finite_mean(ans, LEFT_SLICE),
        "ANS.R_mean": _finite_mean(ans, RIGHT_SLICE),
        "RNS.L_mean": _finite_mean(rns, LEFT_SLICE),
        "RNS.R_mean": _finite_mean(rns, RIGHT_SLICE),
        "ANS.whole_brain_mean": _finite_mean(ans, None),
        "RNS.whole_brain_mean": _finite_mean(rns, None),
    }


def _finite_mean(data: np.ndarray, slices: tuple[slice, slice, slice] | None) -> float:
    values = data[slices] if slices is not None else data
    values = values[np.isfinite(values)]
    return float(values.mean()) if values.size else float("nan")


def _roi_label_to_hemi(label: object) -> str:
    try:
        value = int(label)
    except (TypeError, ValueError):
        return ""
    if 1 <= value <= 180:
        return "L"
    if 1001 <= value <= 1180:
        return "R"
    return ""


def _roi_label_to_compact_index(label: object) -> int | None:
    try:
        value = int(label)
    except (TypeError, ValueError):
        return None
    if 1 <= value <= 180:
        return value
    if 1001 <= value <= 1180:
        return value - 1000
    return None
