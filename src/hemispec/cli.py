from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .api import (
    DGNInferenceConfig,
    DGNModelBundle,
    HemisphereClassificationConfig,
    MetricComputeConfig,
    PipelineRunConfig,
    ValidationConfig,
    compute_metrics,
    discover_local_dgn_bundles,
    resolve_glasser_atlas_path,
    resolve_glasser_label_table,
    run_dgn_inference,
    run_pipeline,
    validate_hemisphere_classification,
    validate_reliability,
    validate_specificity,
)
from .workflow import BilateralWorkflowConfig, run_bilateral_workflow


DEFAULT_FILE_REGEX = r"(sub-MSC\d+).*?(run-\d+)"


def _parse_clip(values: list[float] | None) -> tuple[float, float] | None:
    if values is None:
        return None
    if len(values) != 2:
        raise ValueError("--clip-recon requires exactly two values: LOW HIGH")
    return float(values[0]), float(values[1])


def add_compute_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("compute", help="Compute ANS/RNS maps from GM and DGN-reconstructed GM maps.")
    p.add_argument(
        "--actual-glob",
        required=True,
        help=(
            "Glob for preprocessed actual GM maps. Inputs should be generated with "
            "src/hemispec/resources/preprocess/process_single_subject_GM_v2_reorient.sh "
            "and usually end with _GM_masked.nii.gz."
        ),
    )
    p.add_argument("--predicted-glob", required=True, help="Glob for DGN-reconstructed/predicted GM maps.")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--gm-thresh", type=float, default=0.15)
    p.add_argument("--eps", type=float, default=1e-6)
    p.add_argument("--pred-suffix-to-strip", default="_PRED_LR_full")
    p.add_argument("--actual-suffix-to-strip", default="")
    p.add_argument("--clip-recon", nargs=2, type=float, metavar=("LOW", "HIGH"))
    p.add_argument("--no-voxelwise", action="store_true", help="Do not save group-level voxel-wise NIfTI maps.")
    p.add_argument("--save-subject-maps", action="store_true")
    p.add_argument("--write-nan-outside", action="store_true")
    p.add_argument("--roi-atlas", default=None, help="Optional atlas NIfTI for ROI-wise ANS/RNS export.")
    p.add_argument("--roi-out-csv", default=None, help="ROI-wise output CSV path.")
    p.add_argument("--roi-label-table", default=None, help="Optional atlas label table CSV/TSV/XLSX.")
    p.add_argument("--roi-stat", choices=["mean", "median"], default="mean")
    p.add_argument("--verbose-every", type=int, default=50)
    p.set_defaults(func=cmd_compute)


def add_models_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("models", help="List discoverable local trained DGN model bundles.")
    p.add_argument(
        "--root",
        default=None,
        help="Optional DGN model root override. By default HemiSpec searches local/configured assets/models/dgn.",
    )
    p.set_defaults(func=cmd_models)


def add_infer_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("infer", help="Run trained DGN inference on preprocessed GM maps.")
    p.add_argument("--input-glob", required=True, help="Glob for preprocessed *_GM_masked.nii.gz files.")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--direction", choices=["L_to_R", "R_to_L"], required=True)
    p.add_argument(
        "--model-root",
        default=None,
        help="Optional DGN model root override. By default HemiSpec searches local/configured assets/models/dgn.",
    )
    p.add_argument("--checkpoint", default=None, help="Override checkpoint path.")
    p.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    p.add_argument("--clip-recon", nargs=2, type=float, metavar=("LOW", "HIGH"))
    p.add_argument("--output-suffix", default="_PRED_LR_full.nii.gz")
    p.set_defaults(func=cmd_infer)


def add_run_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("run", help="Run trained DGN inference followed by ANS/RNS compute.")
    p.add_argument("--input-glob", required=True, help="Glob for preprocessed *_GM_masked.nii.gz files.")
    p.add_argument("--recon-dir", required=True, help="Output directory for DGN-reconstructed GM maps.")
    p.add_argument("--metrics-dir", required=True, help="Output directory for ANS/RNS outputs.")
    p.add_argument("--direction", choices=["L_to_R", "R_to_L"], required=True)
    p.add_argument(
        "--model-root",
        default=None,
        help="Optional DGN model root override. By default HemiSpec searches local/configured assets/models/dgn.",
    )
    p.add_argument("--checkpoint", default=None, help="Override checkpoint path.")
    p.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    p.add_argument("--clip-recon", nargs=2, type=float, metavar=("LOW", "HIGH"))
    p.add_argument("--output-suffix", default="_PRED_LR_full.nii.gz")
    p.add_argument("--gm-thresh", type=float, default=0.15)
    p.add_argument("--eps", type=float, default=1e-6)
    p.add_argument("--pred-suffix-to-strip", default="_PRED_LR_full")
    p.add_argument("--actual-suffix-to-strip", default="")
    p.add_argument("--no-voxelwise", action="store_true", help="Do not save group-level voxel-wise NIfTI maps.")
    p.add_argument("--no-subject-maps", action="store_true")
    p.add_argument("--write-nan-outside", action="store_true")
    p.add_argument("--roi-atlas", default=None, help="Optional atlas NIfTI for ROI-wise ANS/RNS export.")
    p.add_argument("--roi-out-csv", default=None, help="ROI-wise output CSV path.")
    p.add_argument("--roi-label-table", default=None, help="Optional atlas label table CSV/TSV/XLSX.")
    p.add_argument("--roi-stat", choices=["mean", "median"], default="mean")
    p.add_argument("--verbose-every", type=int, default=50)
    p.set_defaults(func=cmd_run)


def add_workflow_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "workflow",
        help="Run the full bilateral HemiSpec workflow: L2R/R2L DGN, ANS/RNS, ROI features, classifier, and optional TRT.",
    )
    p.add_argument("--input-glob", required=True, help="Glob for preprocessed *_GM_masked.nii.gz files.")
    p.add_argument("--out-dir", required=True, help="Workflow output directory.")
    p.add_argument(
        "--model-root",
        default=None,
        help="Optional DGN model root override. By default HemiSpec searches local/configured assets/models/dgn.",
    )
    p.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    p.add_argument("--gm-thresh", type=float, default=0.15)
    p.add_argument("--eps", type=float, default=1e-6)
    p.add_argument("--clip-recon", nargs=2, type=float, metavar=("LOW", "HIGH"))
    p.add_argument("--output-suffix", default="_PRED_LR_full.nii.gz")
    p.add_argument("--pred-suffix-to-strip", default="_PRED_LR_full")
    p.add_argument("--actual-suffix-to-strip", default="")
    p.add_argument("--no-voxelwise", action="store_true", help="Do not save direction-level group voxel-wise maps.")
    p.add_argument("--write-zero-outside", action="store_true", help="Write 0 outside valid voxels instead of NaN.")
    p.add_argument("--roi-atlas", default=None, help="Atlas NIfTI for ROI-wise ANS/RNS export. Defaults to a configured/local Glasser atlas.")
    p.add_argument("--roi-label-table", default=None, help="Optional atlas label table. Defaults to a configured/local Glasser label table.")
    p.add_argument("--roi-stat", choices=["mean", "median"], default="mean")
    p.add_argument("--no-classifier", action="store_true", help="Skip saved hemisphere-classifier validation.")
    p.add_argument(
        "--classifier-mode",
        choices=["single", "paired_residual"],
        default="single",
        help="Classifier mode. single is single-hemisphere safe; paired_residual uses paired L/R residual features.",
    )
    p.add_argument("--classifier-model-dir", default=None, help="Optional classifier model directory override.")
    p.add_argument("--classifier-out-dir", default=None, help="Optional classifier output directory override.")
    p.add_argument("--run-trt", action="store_true", help="Run TRT reliability on bilateral subject maps.")
    p.add_argument("--trt-file-regex", default=DEFAULT_FILE_REGEX)
    p.add_argument("--trt-session-a", default="run-01")
    p.add_argument("--trt-session-b", default="run-02")
    p.add_argument("--trt-metric", choices=["pearson", "spearman"], default="pearson")
    p.add_argument("--trt-mask-type", choices=["rate", "max"], default="rate")
    p.add_argument("--trt-thr", type=float, default=0.0)
    p.add_argument("--trt-rate-thr", type=float, default=0.3)
    p.add_argument("--trt-mask-mode", choices=["union", "intersect"], default="union")
    p.add_argument("--trt-no-symmetrize", action="store_true")
    p.add_argument("--trt-no-plots", action="store_true")
    p.add_argument("--verbose-every", type=int, default=50)
    p.set_defaults(func=cmd_workflow)


def add_validation_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--maps-dir", required=True, help="Directory containing per-subject ANS/RNS NIfTI maps.")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--kinds", default="ANS,RNS", help="Comma list, default: ANS,RNS.")
    p.add_argument(
        "--suffix-template",
        default="_{kind}.nii.gz",
        help="Suffix used to select maps for each kind. Use {kind}, default: _{kind}.nii.gz.",
    )
    p.add_argument(
        "--file-regex",
        default=DEFAULT_FILE_REGEX,
        help=(
            "Regex for subject/session parsing. Either named groups (?P<subject>...)(?P<session>...) "
            "or first two groups as subject/session."
        ),
    )
    p.add_argument("--session-a", default="run-01")
    p.add_argument("--session-b", default="run-02")
    p.add_argument(
        "--hemis",
        default="L,R",
        help=(
            "Comma list: L,R,ALL, or auto/target. Use auto/target with --dgn-direction "
            "for one-direction DGN outputs; L_to_R targets R and R_to_L targets L."
        ),
    )
    p.add_argument(
        "--dgn-direction",
        choices=["auto", "L_to_R", "R_to_L", "bilateral"],
        default=None,
        help=(
            "Direction used to resolve --hemis auto/target. auto can infer L_to_R/R_to_L "
            "from maps-dir names such as ANS_RNS_L_to_R."
        ),
    )
    p.add_argument(
        "--hemi-slices",
        default=None,
        help='Custom slices such as "L=60:115,15:134,15:102;R=5:60,15:134,15:102".',
    )
    p.add_argument("--metric", choices=["pearson", "spearman"], default="pearson")
    p.add_argument("--mask-type", choices=["rate", "max"], default="rate")
    p.add_argument("--thr", type=float, default=0.0)
    p.add_argument("--rate-thr", type=float, default=0.3)
    p.add_argument("--mask-mode", choices=["union", "intersect"], default="union")
    p.add_argument("--no-symmetrize", action="store_true")
    p.add_argument("--no-plots", action="store_true")


def add_trt_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("trt", help="Test-retest reliability for ANS/RNS maps.")
    add_validation_common(p)
    p.set_defaults(func=cmd_validate, validation_mode="trt")


def add_specificity_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("specificity", help="Structural specificity validation for ANS/RNS maps.")
    add_validation_common(p)
    p.set_defaults(func=cmd_validate, validation_mode="specificity")


def add_hemi_classify_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "hemi-classify",
        help="Run trained ROI-level hemisphere-classifier validation on computed ANS/RNS features.",
    )
    p.add_argument("--maps-dir", required=True, help="Directory containing computed ANS/RNS maps.")
    p.add_argument("--roi-csv", default=None, help="ROI-wise ANS/RNS CSV produced from an atlas.")
    p.add_argument("--atlas", default=None, help="Atlas NIfTI used to create ROI-wise features.")
    p.add_argument("--label-table", default=None, help="Optional atlas label table.")
    p.add_argument(
        "--classifier-checkpoint",
        default=None,
        help="Trained hemisphere-classifier model directory or single .joblib bundle.",
    )
    p.add_argument(
        "--classifier-model-dir",
        default=None,
        help="Optional classifier model directory override. By default HemiSpec searches local/configured classifier assets.",
    )
    p.add_argument(
        "--classifier-mode",
        choices=["single", "paired_residual"],
        default="single",
        help="Classifier mode. single is single-hemisphere safe; paired_residual requires one L and one R row per subject.",
    )
    p.add_argument("--out-dir", default=None)
    p.add_argument("--kinds", default="ANS,RNS")
    p.add_argument("--suffix-template", default="_{kind}.nii.gz")
    p.add_argument("--file-regex", default=r"(?P<subject>.+?)_{kind}\.nii(?:\.gz)?$")
    p.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    p.add_argument("--batch-size", type=int, default=1)
    p.set_defaults(func=cmd_hemi_classify)


def cmd_compute(args: argparse.Namespace) -> None:
    result = compute_metrics(
        MetricComputeConfig(
            actual_glob=args.actual_glob,
            reconstructed_glob=args.predicted_glob,
            out_dir=Path(args.out_dir),
            gm_thresh=args.gm_thresh,
            eps=args.eps,
            reconstructed_suffix_to_strip=args.pred_suffix_to_strip,
            actual_suffix_to_strip=args.actual_suffix_to_strip,
            clip_recon=_parse_clip(args.clip_recon),
            export_voxelwise=not args.no_voxelwise,
            save_subject_maps=args.save_subject_maps,
            write_nan_outside=args.write_nan_outside,
            verbose_every=args.verbose_every,
            roi_atlas=Path(args.roi_atlas) if args.roi_atlas else None,
            roi_out_csv=Path(args.roi_out_csv) if args.roi_out_csv else None,
            roi_label_table=Path(args.roi_label_table) if args.roi_label_table else None,
            roi_stat=args.roi_stat,
        )
    )
    print("[done] ANS/RNS compute complete")
    for key, value in result.__dict__.items():
        if isinstance(value, list):
            print(f"  {key}: {len(value)}")
        else:
            print(f"  {key}: {value}")


def cmd_models(args: argparse.Namespace) -> None:
    bundles = discover_local_dgn_bundles(args.root)
    if not bundles:
        print("[models] no local DGN bundles found")
        return
    for direction, bundle in bundles.items():
        print(f"[{direction}]")
        print(f"  name: {bundle.name}")
        print(f"  checkpoint: {bundle.checkpoint}")
        print(f"  source: {bundle.source_hemisphere}")
        print(f"  target: {bundle.target_hemisphere}")


def cmd_infer(args: argparse.Namespace) -> None:
    model = _resolve_model_bundle(args)
    outputs = run_dgn_inference(
        DGNInferenceConfig(
            model=model,
            input_glob=args.input_glob,
            out_dir=Path(args.out_dir),
            device=args.device,
            direction=args.direction,
            clip_recon=_parse_clip(args.clip_recon),
            output_suffix=args.output_suffix,
        )
    )
    print("[done] DGN inference complete")
    print(f"  outputs: {len(outputs)}")
    for path in outputs[:5]:
        print(f"  {path}")
    if len(outputs) > 5:
        print(f"  ... {len(outputs) - 5} more")


def cmd_run(args: argparse.Namespace) -> None:
    model = _resolve_model_bundle(args)
    result = run_pipeline(
        PipelineRunConfig(
            inference=DGNInferenceConfig(
                model=model,
                input_glob=args.input_glob,
                out_dir=Path(args.recon_dir),
                device=args.device,
                direction=args.direction,
                clip_recon=_parse_clip(args.clip_recon),
                output_suffix=args.output_suffix,
            ),
            metrics_out_dir=Path(args.metrics_dir),
            gm_thresh=args.gm_thresh,
            eps=args.eps,
            reconstructed_suffix_to_strip=args.pred_suffix_to_strip,
            actual_suffix_to_strip=args.actual_suffix_to_strip,
            export_voxelwise=not args.no_voxelwise,
            save_subject_maps=not args.no_subject_maps,
            write_nan_outside=args.write_nan_outside,
            verbose_every=args.verbose_every,
            roi_atlas=Path(args.roi_atlas) if args.roi_atlas else None,
            roi_out_csv=Path(args.roi_out_csv) if args.roi_out_csv else None,
            roi_label_table=Path(args.roi_label_table) if args.roi_label_table else None,
            roi_stat=args.roi_stat,
        )
    )
    print("[done] DGN inference + ANS/RNS compute complete")
    print(f"  reconstructed: {len(result.reconstructed_paths)}")
    print(f"  pairs: {result.metrics.n_pairs}")
    print(f"  metrics: {result.metrics.out_dir}")
    if result.metrics.subject_maps_dir:
        print(f"  subject_maps: {result.metrics.subject_maps_dir}")
    if result.metrics.roi_csv:
        print(f"  roi_csv: {result.metrics.roi_csv}")


def cmd_workflow(args: argparse.Namespace) -> None:
    try:
        result = run_bilateral_workflow(
            BilateralWorkflowConfig(
                input_glob=args.input_glob,
                out_dir=Path(args.out_dir),
                model_root=Path(args.model_root) if args.model_root else None,
                device=args.device,
                gm_thresh=args.gm_thresh,
                eps=args.eps,
                clip_recon=_parse_clip(args.clip_recon),
                output_suffix=args.output_suffix,
                reconstructed_suffix_to_strip=args.pred_suffix_to_strip,
                actual_suffix_to_strip=args.actual_suffix_to_strip,
                export_voxelwise=not args.no_voxelwise,
                write_nan_outside=not args.write_zero_outside,
                roi_atlas=Path(args.roi_atlas) if args.roi_atlas else None,
                roi_label_table=Path(args.roi_label_table) if args.roi_label_table else None,
                roi_stat=args.roi_stat,
                roi_ignore_zero=True,
                run_classifier=not args.no_classifier,
                classifier_model_dir=Path(args.classifier_model_dir) if args.classifier_model_dir else None,
                classifier_mode=args.classifier_mode,
                classifier_out_dir=Path(args.classifier_out_dir) if args.classifier_out_dir else None,
                run_trt=args.run_trt,
                trt_file_regex=args.trt_file_regex,
                trt_session_a=args.trt_session_a,
                trt_session_b=args.trt_session_b,
                trt_metric=args.trt_metric,
                trt_mask_type=args.trt_mask_type,
                trt_thr=args.trt_thr,
                trt_rate_thr=args.trt_rate_thr,
                trt_mask_mode=args.trt_mask_mode,
                trt_symmetrize=not args.trt_no_symmetrize,
                trt_write_plots=not args.trt_no_plots,
                verbose_every=args.verbose_every,
            )
        )
        print("[done] bilateral HemiSpec workflow complete")
        print(f"  out_dir: {result.out_dir}")
        print(f"  L_to_R reconstructed: {len(result.l_to_r.reconstructed_paths)}")
        print(f"  R_to_L reconstructed: {len(result.r_to_l.reconstructed_paths)}")
        print(f"  bilateral_subject_maps: {result.combined_maps_dir}")
        print(f"  hemisphere_maps: {result.hemi_maps_dir}")
        print(f"  roi_csv: {result.roi_csv}")
        print(f"  roi_wide_csv: {result.roi_wide_csv}")
        print(f"  subject_summary_csv: {result.subject_summary_csv}")
        if result.classifier:
            print(f"  classifier_summary_csv: {result.classifier.summary_csv}")
            if result.classifier.accuracy is not None:
                print(f"  classifier_accuracy_mean: {result.classifier.accuracy:.6f}")
        if result.trt:
            print(f"  trt_summary_csv: {result.trt.summary_csv}")
    except (ImportError, ValueError, RuntimeError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        raise SystemExit(2) from None


def _resolve_model_bundle(args: argparse.Namespace) -> DGNModelBundle:
    if args.checkpoint:
        return DGNModelBundle(
            checkpoint=Path(args.checkpoint),
            direction=args.direction,
            source_hemisphere="left" if args.direction == "L_to_R" else "right",
            target_hemisphere="right" if args.direction == "L_to_R" else "left",
        )
    bundles = discover_local_dgn_bundles(args.model_root)
    if args.direction not in bundles:
        raise RuntimeError(
            f"No local DGN bundle found for {args.direction}. "
            "Use --checkpoint, set HEMISPEC_DGN_MODEL_ROOT, check local assets/models/dgn, or pass --model-root."
        )
    return bundles[args.direction]


def cmd_validate(args: argparse.Namespace) -> None:
    config = ValidationConfig(
        maps_dir=Path(args.maps_dir),
        out_dir=Path(args.out_dir),
        kinds=tuple(x.strip().upper() for x in args.kinds.split(",") if x.strip()),
        suffix_template=args.suffix_template,
        file_regex=args.file_regex,
        session_a=args.session_a,
        session_b=args.session_b,
        hemis=tuple(x.strip().upper() for x in args.hemis.split(",") if x.strip()),
        dgn_direction=args.dgn_direction,
        hemi_slices=args.hemi_slices,
        metric=args.metric,
        mask_type=args.mask_type,
        thr=args.thr,
        rate_thr=args.rate_thr,
        mask_mode=args.mask_mode,
        symmetrize=not args.no_symmetrize,
        write_plots=not args.no_plots,
    )
    run = validate_reliability(config) if getattr(args, "validation_mode", "") == "trt" else validate_specificity(config)
    for row in run.summary_rows:
        label = f"{row.kind}_{row.hemi}"
        print(
            f"[{label}] N={row.n_subjects} vox={row.n_voxels} "
            f"MR={row.match_rate:.1f}% SI={row.specificity_index:.4f} "
            f"t={row.t_value:.2f} p={row.p_value:.2e}"
        )
    print(f"[done] outputs written to {run.out_dir}")


def cmd_hemi_classify(args: argparse.Namespace) -> None:
    try:
        result = validate_hemisphere_classification(
            HemisphereClassificationConfig(
                maps_dir=Path(args.maps_dir),
                roi_csv=Path(args.roi_csv) if args.roi_csv else None,
                atlas_path=Path(args.atlas) if args.atlas else (resolve_glasser_atlas_path() if not args.roi_csv else None),
                label_table=Path(args.label_table) if args.label_table else (resolve_glasser_label_table() if not args.roi_csv else None),
                classifier_checkpoint=Path(args.classifier_checkpoint) if args.classifier_checkpoint else None,
                classifier_model_dir=Path(args.classifier_model_dir) if args.classifier_model_dir else None,
                classifier_mode=args.classifier_mode,
                out_dir=Path(args.out_dir) if args.out_dir else None,
                kinds=tuple(x.strip().upper() for x in args.kinds.split(",") if x.strip()),
                suffix_template=args.suffix_template,
                file_regex=args.file_regex,
                device=args.device,
                batch_size=args.batch_size,
            )
        )
        print(result.message)
        if result.accuracy is not None:
            print(f"accuracy_mean: {result.accuracy:.6f}")
        print(f"n_samples: {result.n_samples}")
        if result.summary_csv:
            print(f"summary_csv: {result.summary_csv}")
        if result.predictions_csv:
            print(f"predictions_csv: {result.predictions_csv}")
    except (NotImplementedError, ImportError, ValueError, RuntimeError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        raise SystemExit(2) from None


def build_parser(prog: str | None = None) -> argparse.ArgumentParser:
    if prog is None:
        prog = Path(sys.argv[0]).stem or "hemispec"
        if prog == "__main__":
            prog = "hemispec"
    parser = argparse.ArgumentParser(
        prog=prog,
        description="HemiSpec: reconstruction-derived hemispheric specificity toolkit.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    add_models_parser(sub)
    add_infer_parser(sub)
    add_run_parser(sub)
    add_workflow_parser(sub)
    add_compute_parser(sub)
    add_trt_parser(sub)
    add_specificity_parser(sub)
    add_hemi_classify_parser(sub)
    return parser


def main(argv: list[str] | None = None, prog: str | None = None) -> None:
    parser = build_parser(prog=prog)
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
