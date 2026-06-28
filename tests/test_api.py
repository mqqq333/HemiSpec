from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
import pytest
import hemispec.api as api
import hemispec.cli as cli
import hemispec.gui as gui_module

from hemispec import (
    BilateralWorkflowConfig,
    DGNInferenceConfig,
    DGNModelBundle,
    HemisphereClassificationConfig,
    MetricComputeConfig,
    PipelineRunConfig,
    compute_metrics,
    discover_local_dgn_bundles,
    get_preprocessing_spec,
    infer_dgn_direction_from_path,
    resolve_validation_hemis,
    resolve_classifier_model_dir,
    resolve_dgn_model_root,
    resolve_glasser_atlas_path,
    resolve_glasser_label_table,
    run_dgn_inference,
    run_pipeline,
    target_hemisphere_for_direction,
    validate_specificity,
    validate_hemisphere_classification,
    ValidationConfig,
)
import hemispec.workflow as workflow
from hemispec.dgn_inference import crop_source, paste_prediction
from hemispec.gui import HemiSpecGui
from hemispec.hemisphere_classifier import apply_classifier_feature_transform, build_classifier_feature_table
from hemispec.workflow import run_bilateral_workflow, summarize_bilateral_roi_features, summarize_subject_metrics
from hemispec.roi import RoiSummaryConfig, summarize_maps_by_atlas


def _save(path: Path, arr: np.ndarray) -> None:
    nib.save(nib.Nifti1Image(arr.astype(np.float32), np.eye(4)), str(path))


def test_preprocessing_spec_points_to_project_files():
    spec = get_preprocessing_spec(Path.cwd())
    assert spec.script_path.name == "process_single_subject_GM_v2_reorient.sh"
    assert spec.script_path.exists()
    assert spec.sample_input_dir is not None
    assert spec.sample_input_dir.name == "input_sample"
    assert spec.sample_input_dir.parent.name == "examples"
    assert spec.output_suffix == "_GM_masked.nii.gz"
    assert spec.gm_threshold == 0.15


def test_compute_metrics_api_smoke(tmp_path):
    gm_dir = tmp_path / "gm"
    recon_dir = tmp_path / "recon"
    out_dir = tmp_path / "metrics"
    gm_dir.mkdir()
    recon_dir.mkdir()

    gm = np.full((4, 4, 4), 0.2, dtype=np.float32)
    recon = np.full((4, 4, 4), 0.1, dtype=np.float32)
    _save(gm_dir / "sub-01_GM_masked.nii.gz", gm)
    _save(recon_dir / "sub-01_GM_masked_PRED_LR_full.nii.gz", recon)

    result = compute_metrics(
        MetricComputeConfig(
            actual_glob=str(gm_dir / "*.nii.gz"),
            reconstructed_glob=str(recon_dir / "*.nii.gz"),
            out_dir=out_dir,
            save_subject_maps=True,
            verbose_every=0,
        )
    )

    assert result.n_pairs == 1
    assert result.n_reconstructed == 1
    assert result.subject_maps_dir == out_dir / "subject_maps"
    assert (out_dir / "ANS_group_masked_mean.nii.gz").exists()
    assert (out_dir / "subject_maps" / "sub-01_GM_masked_ANS.nii.gz").exists()


def test_compute_metrics_roiwise_export(tmp_path):
    gm_dir = tmp_path / "gm"
    recon_dir = tmp_path / "recon"
    out_dir = tmp_path / "metrics"
    gm_dir.mkdir()
    recon_dir.mkdir()

    gm = np.full((4, 4, 4), 0.2, dtype=np.float32)
    recon = np.full((4, 4, 4), 0.1, dtype=np.float32)
    atlas = np.zeros((4, 4, 4), dtype=np.int16)
    atlas[:2] = 1
    atlas[2:] = 2
    _save(gm_dir / "sub-01_GM_masked.nii.gz", gm)
    _save(recon_dir / "sub-01_GM_masked_PRED_LR_full.nii.gz", recon)
    nib.save(nib.Nifti1Image(atlas, np.eye(4)), str(tmp_path / "atlas.nii.gz"))

    result = compute_metrics(
        MetricComputeConfig(
            actual_glob=str(gm_dir / "*.nii.gz"),
            reconstructed_glob=str(recon_dir / "*.nii.gz"),
            out_dir=out_dir,
            roi_atlas=tmp_path / "atlas.nii.gz",
            export_voxelwise=False,
            verbose_every=0,
        )
    )

    assert result.subject_maps_dir == out_dir / "subject_maps"
    assert result.roi_csv == out_dir / "roi_summary.csv"
    assert result.roi_csv.exists()
    roi = pd.read_csv(result.roi_csv)
    assert set(roi["roi_label"]) == {1, 2}
    assert set(roi["kind"]) == {"ANS", "RNS"}
    assert not (out_dir / "ANS_group_masked_mean.nii.gz").exists()


def test_roi_summary_ignores_zero_voxels_by_default(tmp_path):
    maps_dir = tmp_path / "maps"
    maps_dir.mkdir()
    data = np.array([[[0.0, 2.0], [4.0, 0.0]]], dtype=np.float32)
    atlas = np.ones(data.shape, dtype=np.int16)
    _save(maps_dir / "sub-01_ANS.nii.gz", data)
    nib.save(nib.Nifti1Image(atlas, np.eye(4)), str(tmp_path / "atlas.nii.gz"))

    out = summarize_maps_by_atlas(
        RoiSummaryConfig(
            maps_glob=str(maps_dir / "*.nii.gz"),
            atlas_path=tmp_path / "atlas.nii.gz",
            out_csv=tmp_path / "roi.csv",
        )
    )

    row = out.iloc[0]
    assert row["value"] == 3.0
    assert row["n_voxels"] == 2


def test_validate_specificity_api_smoke(tmp_path):
    subjects = ["sub-MSC01", "sub-MSC02", "sub-MSC03"]
    for i, subject in enumerate(subjects):
        base = np.zeros((4, 4, 4), dtype=np.float32)
        base.flat[i * 5 : i * 5 + 5] = 1.0
        _save(tmp_path / f"{subject}_run-01_ANS.nii.gz", base)
        _save(tmp_path / f"{subject}_run-02_ANS.nii.gz", base + 0.01)

    result = validate_specificity(
        ValidationConfig(
            maps_dir=tmp_path,
            out_dir=tmp_path / "specificity",
            kinds=("ANS",),
            hemis=("ALL",),
            mask_type="rate",
            rate_thr=0.1,
            symmetrize=False,
            write_plots=False,
        )
    )

    assert len(result.results) == 1
    assert result.summary_csv is not None
    assert result.summary_csv.exists()
    assert result.summary_rows[0].match_rate == 100.0
    assert list(result.to_dataframe()["kind"]) == ["ANS"]


def test_dgn_inference_api_wires_runtime(monkeypatch, tmp_path):
    calls = {}

    def fake_resolve_device(device):
        calls["device_arg"] = device
        return "cpu"

    def fake_load_generator(checkpoint, device):
        calls["checkpoint"] = checkpoint
        calls["device"] = device
        return object()

    def fake_run_dgn_inference_files(**kwargs):
        calls.update(kwargs)

        class Output:
            output_path = tmp_path / "sub-01_PRED_LR_full.nii.gz"

        return [Output()]

    monkeypatch.setattr(api, "resolve_device", fake_resolve_device)
    monkeypatch.setattr(api, "load_generator", fake_load_generator)
    monkeypatch.setattr(api, "run_dgn_inference_files", fake_run_dgn_inference_files)

    config = DGNInferenceConfig(
        model=DGNModelBundle(checkpoint=tmp_path / "model.pth", direction="L_to_R"),
        input_glob=str(tmp_path / "*.nii.gz"),
        out_dir=tmp_path / "recon",
        device="auto",
    )

    outputs = run_dgn_inference(config)

    assert outputs == [tmp_path / "sub-01_PRED_LR_full.nii.gz"]
    assert calls["device_arg"] == "auto"
    assert calls["checkpoint"] == tmp_path / "model.pth"
    assert calls["direction"] == "L_to_R"


def test_dgn_inference_requires_direction_for_unlabeled_model(tmp_path):
    config = DGNInferenceConfig(
        model=DGNModelBundle(checkpoint=tmp_path / "model.pth"),
        input_glob=str(tmp_path / "*.nii.gz"),
        out_dir=tmp_path / "recon",
    )
    with pytest.raises(ValueError, match="model.direction"):
        run_dgn_inference(config)


def test_pipeline_api_runs_inference_then_metrics(monkeypatch, tmp_path):
    calls = {}
    recon_dir = tmp_path / "recon"
    metrics_dir = tmp_path / "metrics"

    def fake_run_dgn_inference(config):
        calls["inference"] = config
        recon_dir.mkdir()
        output = recon_dir / "sub-01_GM_masked_PRED_LR_full.nii.gz"
        output.write_bytes(b"")
        return [output]

    def fake_compute_metrics(config):
        calls["metrics"] = config

        return api.MetricComputeResult(
            n_actual=1,
            n_reconstructed=1,
            n_pairs=1,
            missing_actual=[],
            missing_reconstructed=[],
            out_dir=config.out_dir,
            subject_maps_dir=config.out_dir / "subject_maps",
        )

    monkeypatch.setattr(api, "run_dgn_inference", fake_run_dgn_inference)
    monkeypatch.setattr(api, "compute_metrics", fake_compute_metrics)

    inference = DGNInferenceConfig(
        model=DGNModelBundle(checkpoint=tmp_path / "model.pth", direction="L_to_R"),
        input_glob=str(tmp_path / "gm" / "*_GM_masked.nii.gz"),
        out_dir=recon_dir,
        direction="L_to_R",
    )
    result = run_pipeline(PipelineRunConfig(inference=inference, metrics_out_dir=metrics_dir))

    assert result.reconstructed_paths == [recon_dir / "sub-01_GM_masked_PRED_LR_full.nii.gz"]
    assert result.metrics.n_pairs == 1
    assert calls["metrics"].actual_glob == inference.input_glob
    assert calls["metrics"].reconstructed_glob == str(recon_dir / "*_PRED_LR_full.nii.gz")
    assert calls["metrics"].save_subject_maps is True


def test_subject_metric_summary_reports_hemi_and_whole_brain_means(tmp_path):
    maps_dir = tmp_path / "maps"
    maps_dir.mkdir()
    ans = np.full((115, 134, 102), np.nan, dtype=np.float32)
    rns = np.full((115, 134, 102), np.nan, dtype=np.float32)
    ans[60:115, 15:134, 15:102] = 1.0
    ans[5:60, 15:134, 15:102] = 3.0
    rns[60:115, 15:134, 15:102] = 2.0
    rns[5:60, 15:134, 15:102] = 4.0
    _save(maps_dir / "sub-01_ANS.nii.gz", ans)
    _save(maps_dir / "sub-01_RNS.nii.gz", rns)

    summary = summarize_subject_metrics(maps_dir, tmp_path / "summary.csv")

    row = summary.iloc[0]
    assert row["subject"] == "sub-01"
    assert row["ANS.L_mean"] == 1.0
    assert row["ANS.R_mean"] == 3.0
    assert row["RNS.L_mean"] == 2.0
    assert row["RNS.R_mean"] == 4.0
    assert row["ANS.whole_brain_mean"] == 2.0
    assert row["RNS.whole_brain_mean"] == 3.0


def test_bilateral_workflow_merges_directions_and_runs_optional_steps(monkeypatch, tmp_path):
    gm_dir = tmp_path / "gm"
    gm_dir.mkdir()
    _save(gm_dir / "sub-MSC01_run-01_GM_masked.nii.gz", np.ones((115, 134, 102), dtype=np.float32))

    atlas = np.zeros((115, 134, 102), dtype=np.int16)
    atlas[60:115, 15:134, 15:102] = 1
    atlas[5:60, 15:134, 15:102] = 1001
    _save(tmp_path / "atlas.nii.gz", atlas)
    classifier_calls = {}
    trt_calls = {}

    def fake_discover(_root=None):
        return {
            "L_to_R": DGNModelBundle(checkpoint=tmp_path / "l2r.pth", direction="L_to_R"),
            "R_to_L": DGNModelBundle(checkpoint=tmp_path / "r2l.pth", direction="R_to_L"),
        }

    def fake_run_pipeline(config):
        direction = config.inference.direction
        subject_dir = config.metrics_out_dir / "subject_maps"
        subject_dir.mkdir(parents=True)
        ans = np.full((115, 134, 102), np.nan, dtype=np.float32)
        rns = np.full((115, 134, 102), np.nan, dtype=np.float32)
        if direction == "L_to_R":
            ans[5:60, 15:134, 15:102] = 3.0
            rns[5:60, 15:134, 15:102] = 4.0
        else:
            ans[60:115, 15:134, 15:102] = 1.0
            rns[60:115, 15:134, 15:102] = 2.0
        _save(subject_dir / "sub-MSC01_run-01_GM_masked_ANS.nii.gz", ans)
        _save(subject_dir / "sub-MSC01_run-01_GM_masked_RNS.nii.gz", rns)
        return api.PipelineRunResult(
            reconstructed_paths=[config.inference.out_dir / "sub-MSC01_run-01_GM_masked_PRED_LR_full.nii.gz"],
            metrics=api.MetricComputeResult(
                n_actual=1,
                n_reconstructed=1,
                n_pairs=1,
                missing_actual=[],
                missing_reconstructed=[],
                out_dir=config.metrics_out_dir,
                subject_maps_dir=subject_dir,
                roi_csv=config.roi_out_csv,
            ),
        )

    def fake_classifier(config):
        classifier_calls["config"] = config
        return api.HemisphereClassificationResult(
            accuracy=1.0,
            n_samples=2,
            summary_csv=config.out_dir / "summary.csv" if config.out_dir else None,
            predictions_csv=config.out_dir / "predictions.csv" if config.out_dir else None,
            out_dir=config.out_dir,
            message="ok",
        )

    def fake_trt(config):
        trt_calls["config"] = config
        return api.ValidationRunResult(summary_csv=config.out_dir / "validation_summary.csv", out_dir=config.out_dir)

    monkeypatch.setattr(workflow, "discover_local_dgn_bundles", fake_discover)
    monkeypatch.setattr(workflow, "run_pipeline", fake_run_pipeline)
    monkeypatch.setattr(workflow, "validate_hemisphere_classification", fake_classifier)
    monkeypatch.setattr(workflow, "validate_reliability", fake_trt)

    result = run_bilateral_workflow(
        BilateralWorkflowConfig(
            input_glob=str(gm_dir / "*.nii.gz"),
            out_dir=tmp_path / "workflow",
            roi_atlas=tmp_path / "atlas.nii.gz",
            run_classifier=True,
            run_trt=True,
            verbose_every=0,
        )
    )

    assert (result.combined_maps_dir / "sub-MSC01_run-01_GM_masked_ANS.nii.gz").exists()
    assert (result.hemi_maps_dir / "sub-MSC01_run-01_GM_masked_ANS.L.nii.gz").exists()
    assert (result.hemi_maps_dir / "sub-MSC01_run-01_GM_masked_RNS.R.nii.gz").exists()
    summary = pd.read_csv(result.subject_summary_csv)
    row = summary.iloc[0]
    assert row["ANS.L_mean"] == 1.0
    assert row["ANS.R_mean"] == 3.0
    assert row["RNS.L_mean"] == 2.0
    assert row["RNS.R_mean"] == 4.0
    roi = pd.read_csv(result.roi_csv)
    assert set(roi["kind"]) == {"ANS", "RNS"}
    assert set(roi["roi_label"]) == {1, 1001}
    assert set(roi["metric_hemi"]) == {"ANS.L", "ANS.R", "RNS.L", "RNS.R"}
    assert set(roi["feature_name"]) == {"ANS.L_roi_1", "ANS.R_roi_1", "RNS.L_roi_1", "RNS.R_roi_1"}
    wide = pd.read_csv(result.roi_wide_csv)
    assert set(wide.columns) == {"subject", "ANS.L_roi_1", "ANS.R_roi_1", "RNS.L_roi_1", "RNS.R_roi_1"}
    assert classifier_calls["config"].roi_csv == result.roi_csv
    assert trt_calls["config"].maps_dir == result.combined_maps_dir
    assert trt_calls["config"].hemis == ("L", "R")


def test_summarize_bilateral_roi_features_writes_explicit_metric_hemi_tables(tmp_path):
    roi_csv = tmp_path / "roi.csv"
    pd.DataFrame(
        [
            {"subject": "sub-01", "kind": "ANS", "roi_label": 1, "value": 1.0},
            {"subject": "sub-01", "kind": "ANS", "roi_label": 1001, "value": 2.0},
            {"subject": "sub-01", "kind": "RNS", "roi_label": 1, "value": 3.0},
            {"subject": "sub-01", "kind": "RNS", "roi_label": 1001, "value": 4.0},
        ]
    ).to_csv(roi_csv, index=False)

    annotated = summarize_bilateral_roi_features(roi_csv, tmp_path / "wide.csv")

    assert set(annotated["metric_hemi"]) == {"ANS.L", "ANS.R", "RNS.L", "RNS.R"}
    wide = pd.read_csv(tmp_path / "wide.csv")
    row = wide.iloc[0]
    assert row["ANS.L_roi_1"] == 1.0
    assert row["ANS.R_roi_1"] == 2.0
    assert row["RNS.L_roi_1"] == 3.0
    assert row["RNS.R_roi_1"] == 4.0


def test_cli_trt_dispatches_to_reliability(monkeypatch, tmp_path):
    calls = []

    def fake_reliability(config):
        calls.append(("reliability", config))
        return api.ValidationRunResult(summary_rows=[], summary_csv=config.out_dir / "validation_summary.csv", out_dir=config.out_dir)

    def fake_specificity(config):
        calls.append(("specificity", config))
        return api.ValidationRunResult(summary_rows=[], summary_csv=config.out_dir / "validation_summary.csv", out_dir=config.out_dir)

    monkeypatch.setattr(cli, "validate_reliability", fake_reliability)
    monkeypatch.setattr(cli, "validate_specificity", fake_specificity)

    parser = cli.build_parser()
    args = parser.parse_args(
        [
            "trt",
            "--maps-dir",
            str(tmp_path),
            "--out-dir",
            str(tmp_path / "trt"),
            "--no-plots",
        ]
    )
    args.func(args)

    assert calls[0][0] == "reliability"


def test_gui_trt_dispatches_to_reliability(monkeypatch):
    calls = []

    def fake_reliability(config):
        calls.append(("reliability", config))
        return api.ValidationRunResult(summary_rows=[], summary_csv=config.out_dir / "validation_summary.csv", out_dir=config.out_dir)

    def fake_specificity(config):
        calls.append(("specificity", config))
        return api.ValidationRunResult(summary_rows=[], summary_csv=config.out_dir / "validation_summary.csv", out_dir=config.out_dir)

    monkeypatch.setattr(gui_module, "validate_reliability", fake_reliability)
    monkeypatch.setattr(gui_module, "validate_specificity", fake_specificity)

    app = HemiSpecGui()
    try:
        app._run_background = lambda _label, fn: fn()
        app._run_validation(app.trt_vars)
        assert calls[0][0] == "reliability"
    finally:
        app.destroy()


def test_hemisphere_classification_uses_default_model_and_requires_features(tmp_path):
    with pytest.raises(ValueError, match="roi_csv"):
        validate_hemisphere_classification(
            HemisphereClassificationConfig(
                maps_dir=tmp_path,
            )
        )


def test_hemisphere_classifier_pivots_roi_summary_to_left_right_features():
    rows = []
    for subject in ("sub-01", "sub-02"):
        for kind in ("ANS", "RNS"):
            for label in (1, 2, 1001, 1002):
                rows.append(
                    {
                        "subject": subject,
                        "kind": kind,
                        "roi_label": label,
                        "value": float(label) if label < 1000 else float(label - 1000 + 10),
                    }
                )
    table = pd.DataFrame(rows)
    features = ["GLS_ANS_roi_1", "GLS_ANS_roi_2"]

    out = build_classifier_feature_table(table, "ANS", features)

    assert list(out.columns[:5]) == ["subject", "hemi", "y_true", "GLS_ANS_roi_1", "GLS_ANS_roi_2"]
    assert list(out["subject"]) == ["sub-01", "sub-02", "sub-01", "sub-02"]
    assert list(out["hemi"]) == ["L", "L", "R", "R"]
    assert list(out["y_true"]) == [0, 0, 1, 1]
    assert list(out["GLS_ANS_roi_1"]) == [1.0, 1.0, 11.0, 11.0]


def test_hemisphere_classifier_preserves_all_nan_roi_columns_for_imputer():
    table = pd.DataFrame(
        [
            {"subject": "sub-01", "kind": "ANS", "roi_label": 1, "value": 1.0},
            {"subject": "sub-01", "kind": "ANS", "roi_label": 2, "value": np.nan},
            {"subject": "sub-01", "kind": "ANS", "roi_label": 1001, "value": 11.0},
            {"subject": "sub-01", "kind": "ANS", "roi_label": 1002, "value": np.nan},
        ]
    )

    out = build_classifier_feature_table(table, "ANS", ["GLS_ANS_roi_1", "GLS_ANS_roi_2"])

    assert list(out["GLS_ANS_roi_1"]) == [1.0, 11.0]
    assert np.isnan(out.loc[0, "GLS_ANS_roi_2"])
    assert np.isnan(out.loc[1, "GLS_ANS_roi_2"])


def test_hemisphere_classifier_subject_lr_residual_zscore_requires_pairs():
    table = pd.DataFrame(
        {
            "subject": ["sub-01", "sub-01"],
            "hemi": ["L", "R"],
            "y_true": [0, 1],
            "GLS_ANS_roi_1": [1.0, 3.0],
            "GLS_ANS_roi_2": [2.0, 6.0],
        }
    )

    out = apply_classifier_feature_transform(
        table,
        ["GLS_ANS_roi_1", "GLS_ANS_roi_2"],
        "subject_lr_residual_zscore",
    )

    assert np.allclose(out.loc[0, ["GLS_ANS_roi_1", "GLS_ANS_roi_2"]], [-0.6324555, -1.264911], atol=1e-6)
    assert np.allclose(out.loc[1, ["GLS_ANS_roi_1", "GLS_ANS_roi_2"]], [0.6324555, 1.264911], atol=1e-6)

    unpaired = table.iloc[:1].copy()
    with pytest.raises(ValueError, match="requires exactly one L and one R row"):
        apply_classifier_feature_transform(unpaired, ["GLS_ANS_roi_1", "GLS_ANS_roi_2"], "subject_lr_residual_zscore")


def test_discover_local_dgn_bundles_uses_packaged_asset_layout(tmp_path):
    model_root = tmp_path / "assets" / "models" / "dgn"
    left_ckpt_dir = model_root / "outputs_bi_stable_L" / "ckpts"
    right_ckpt_dir = model_root / "outputs_bi_stable_R" / "ckpts"
    left_ckpt_dir.mkdir(parents=True)
    right_ckpt_dir.mkdir(parents=True)
    (left_ckpt_dir / "best_netG_L.pth").write_bytes(b"")
    (right_ckpt_dir / "best_netG_R.pth").write_bytes(b"")

    bundles = discover_local_dgn_bundles(tmp_path)

    assert bundles["R_to_L"].checkpoint.name == "best_netG_L.pth"
    assert bundles["R_to_L"].checkpoint.parent == left_ckpt_dir
    assert bundles["R_to_L"].source_hemisphere == "right"
    assert bundles["R_to_L"].target_hemisphere == "left"
    assert bundles["L_to_R"].checkpoint.name == "best_netG_R.pth"
    assert bundles["L_to_R"].checkpoint.parent == right_ckpt_dir
    assert bundles["L_to_R"].source_hemisphere == "left"
    assert bundles["L_to_R"].target_hemisphere == "right"
    assert not hasattr(bundles["L_to_R"], "reference_code_dir")
    assert not hasattr(bundles["L_to_R"], "runtime_code_dir")


def test_discover_local_dgn_bundles_keeps_legacy_root_layout_compatible(tmp_path):
    left_ckpt_dir = tmp_path / "outputs_bi_stable_L" / "ckpts"
    right_ckpt_dir = tmp_path / "outputs_bi_stable_R" / "ckpts"
    left_ckpt_dir.mkdir(parents=True)
    right_ckpt_dir.mkdir(parents=True)
    (left_ckpt_dir / "best_netG_L.pth").write_bytes(b"")
    (right_ckpt_dir / "best_netG_R.pth").write_bytes(b"")

    bundles = discover_local_dgn_bundles(tmp_path)

    assert bundles["R_to_L"].checkpoint.parent == left_ckpt_dir
    assert bundles["L_to_R"].checkpoint.parent == right_ckpt_dir


def test_discover_local_dgn_bundles_prefers_explicit_direction_checkpoint_names(tmp_path):
    model_root = tmp_path / "assets" / "models" / "dgn"
    left_ckpt_dir = model_root / "outputs_bi_stable_L" / "ckpts"
    right_ckpt_dir = model_root / "outputs_bi_stable_R" / "ckpts"
    left_ckpt_dir.mkdir(parents=True)
    right_ckpt_dir.mkdir(parents=True)
    (left_ckpt_dir / "best_netG_L.pth").write_bytes(b"")
    (left_ckpt_dir / "best_netG_R2L.pth").write_bytes(b"")
    (right_ckpt_dir / "best_netG_R.pth").write_bytes(b"")
    (right_ckpt_dir / "best_netG_L2R.pth").write_bytes(b"")

    bundles = discover_local_dgn_bundles(tmp_path)

    assert bundles["R_to_L"].checkpoint.name == "best_netG_R2L.pth"
    assert bundles["L_to_R"].checkpoint.name == "best_netG_L2R.pth"


def test_default_asset_resolvers_find_local_project_assets():
    model_root = resolve_dgn_model_root()
    classifier_dir = resolve_classifier_model_dir()
    atlas_path = resolve_glasser_atlas_path()
    label_table = resolve_glasser_label_table()

    assert model_root.parts[-3:] == ("assets", "models", "dgn")
    assert (model_root / "outputs_bi_stable_L" / "ckpts").exists()
    assert classifier_dir.name == "OUT_noICBM_train_ICBM_external_saved_models"
    assert atlas_path.name == "MNI_Glasser_HCP_v1.0_1p5mm.nii.gz"
    assert label_table.name == "Glasser_label_index_mapping.xlsx"


def test_dgn_crop_and_paste_direction_mapping():
    volume = np.zeros((115, 134, 102), dtype=np.float32)
    volume[60:115, 15:134, 15:102] = 1.0
    volume[5:60, 15:134, 15:102] = 2.0

    left_source = crop_source(volume, "L_to_R")
    right_source = crop_source(volume, "R_to_L")
    assert left_source.shape == (55, 119, 87)
    assert right_source.shape == (55, 119, 87)
    assert np.all(left_source == 1.0)
    assert np.all(right_source == 2.0)

    generated = np.full((55, 119, 87), 7.0, dtype=np.float32)
    out = paste_prediction(volume, generated, "L_to_R", mask_target=False)
    assert np.all(out[5:60, 15:134, 15:102] == 7.0)
    assert np.all(out[60:115, 15:134, 15:102] == 1.0)


def test_validation_target_hemisphere_resolution():
    assert target_hemisphere_for_direction("L_to_R") == "R"
    assert target_hemisphere_for_direction("R_to_L") == "L"
    assert target_hemisphere_for_direction("bilateral") is None

    assert infer_dgn_direction_from_path("TRT_outputs/ANS_RNS_L_to_R/subject_maps") == "L_to_R"
    assert infer_dgn_direction_from_path("TRT_outputs/ANS_RNS_R_to_L/subject_maps") == "R_to_L"

    assert resolve_validation_hemis(("target",), "L_to_R") == ("R",)
    assert resolve_validation_hemis(("auto",), "R_to_L") == ("L",)
    assert resolve_validation_hemis(("auto",), maps_dir="TRT_outputs/ANS_RNS_L_to_R/subject_maps") == ("R",)
    assert resolve_validation_hemis(("auto",), "bilateral") == ("L", "R")
    assert resolve_validation_hemis(("L", "R"), "L_to_R") == ("L", "R")

    with pytest.raises(ValueError, match="hemis=target"):
        resolve_validation_hemis(("target",), "auto", maps_dir="unknown")


def test_gui_has_workbench_pages_and_defaults():
    app = HemiSpecGui()
    try:
        assert set(app.pages) == {"workflow", "pipeline", "infer", "compute", "trt", "hemi_classify", "specificity"}
        assert app.active_page == "workflow"
        assert app.page_title_var.get() == "Full Workflow"
        assert app.workflow_vars["run_classifier"].get() is True
        assert app.workflow_vars["run_trt"].get() is False
        assert app.pipeline_vars["direction"].get() == "L_to_R"
        assert Path(app.pipeline_vars["model_root"].get()).parts[-3:] == ("assets", "models", "dgn")
        assert app.pipeline_vars["roi_stat"].get() == "mean"
        assert app.trt_vars["hemis"].get() == "auto"
        assert app.trt_vars["dgn_direction"].get() == "auto"
        app._show_page("hemi_classify")
        assert app.active_page == "hemi_classify"
        assert app.page_title_var.get() == "Hemisphere Classifier"
        assert app.hemi_classify_vars["classifier_model_dir"].get().endswith(
            "OUT_noICBM_train_ICBM_external_saved_models"
        )
    finally:
        app.destroy()


def test_gui_builds_public_api_configs():
    app = HemiSpecGui()
    try:
        workflow_config = app._workflow_config(app.workflow_vars)
        assert isinstance(workflow_config, BilateralWorkflowConfig)
        assert workflow_config.run_classifier is True
        assert workflow_config.run_trt is False
        assert workflow_config.write_nan_outside is True
        assert workflow_config.roi_atlas is not None

        pipeline = app._pipeline_config(app.pipeline_vars)
        assert isinstance(pipeline, PipelineRunConfig)
        assert pipeline.inference.direction == "L_to_R"
        assert pipeline.inference.model.direction == "L_to_R"
        assert pipeline.inference.model.target_hemisphere == "right"
        assert pipeline.inference.model.checkpoint.exists()
        assert pipeline.roi_atlas is not None
        assert pipeline.roi_atlas.name == "MNI_Glasser_HCP_v1.0_1p5mm.nii.gz"
        assert "assets" in pipeline.roi_atlas.parts
        assert pipeline.save_subject_maps is True

        validation = app._validation_config(app.trt_vars)
        assert isinstance(validation, ValidationConfig)
        assert validation.hemis == ("AUTO",)
        assert validation.dgn_direction == "auto"
        assert validation.session_a == "run-01"
        assert validation.session_b == "run-02"

        classifier = app._hemi_classification_config(app.hemi_classify_vars)
        assert isinstance(classifier, HemisphereClassificationConfig)
        assert classifier.classifier_model_dir is not None
        assert classifier.classifier_model_dir.name == "OUT_noICBM_train_ICBM_external_saved_models"
        assert classifier.kinds == ("ANS", "RNS")
    finally:
        app.destroy()
