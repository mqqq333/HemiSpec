from pathlib import Path

import hemispec.cli as cli
import hemispec.gui as gui_module
from hemispec.gui import (
    ENCAPSULATED_DEFAULTS,
    WORKFLOW_ENCAPSULATED_FIELDS,
    WORKFLOW_REQUIRED_FIELDS,
    WORKFLOW_VISIBLE_FIELDS,
    build_runtime_asset_status,
    make_workflow_config,
    runtime_mode_label,
    workflow_cli_command,
)


def _state(**overrides: object) -> dict[str, object]:
    state: dict[str, object] = {
        "input_glob": "E:/data/**/*_GM_masked.nii.gz",
        "out_dir": "E:/out/HemiSpec Run",
        "export_roi_table": True,
        "roi_atlas": "E:/atlas/glasser.nii.gz",
        "roi_label_table": "E:/atlas/labels.xlsx",
        "run_classifier": False,
        "run_trt": False,
    }
    state.update(ENCAPSULATED_DEFAULTS)
    state.update(overrides)
    return state


def test_standard_workflow_exposes_only_user_decisions() -> None:
    assert WORKFLOW_VISIBLE_FIELDS == (
        "input_glob",
        "out_dir",
        "export_roi_table",
        "roi_atlas",
        "roi_label_table",
        "run_classifier",
        "run_trt",
    )


def test_standard_workflow_encapsulates_model_assets_and_internal_parameters() -> None:
    encapsulated = set(WORKFLOW_ENCAPSULATED_FIELDS)
    assert {"model_root", "device", "classifier_model_dir"}.issubset(encapsulated)
    assert {"gm_thresh", "eps", "pred_suffix", "actual_suffix", "trt_file_regex", "roi_stat"}.issubset(encapsulated)
    assert encapsulated.isdisjoint(WORKFLOW_VISIBLE_FIELDS)


def test_standard_workflow_field_contract_has_no_duplicates() -> None:
    assert len(WORKFLOW_REQUIRED_FIELDS) == len(set(WORKFLOW_REQUIRED_FIELDS))
    assert set(WORKFLOW_REQUIRED_FIELDS) == set(WORKFLOW_VISIBLE_FIELDS) | set(WORKFLOW_ENCAPSULATED_FIELDS)


def test_classifier_forces_roi_export_in_config() -> None:
    config = make_workflow_config(
        _state(export_roi_table=False, run_classifier=True, roi_atlas="", roi_label_table="")
    )
    assert config.export_roi_table is True
    assert config.run_classifier is True


def test_no_roi_flag_is_preserved_when_classifier_is_off() -> None:
    config = make_workflow_config(_state(export_roi_table=False, run_classifier=False))
    assert config.export_roi_table is False
    assert config.roi_atlas is None
    assert config.roi_label_table is None


def test_gui_accepts_input_directory_as_gm_glob(tmp_path: Path) -> None:
    config = make_workflow_config(_state(input_glob=str(tmp_path), export_roi_table=False))

    assert config.input_glob == str(tmp_path / "*_GM_masked.nii.gz")


def test_gui_state_to_cli_command_quotes_paths_and_flags(tmp_path: Path) -> None:
    atlas = tmp_path / "glasser.nii.gz"
    labels = tmp_path / "labels.xlsx"
    atlas.write_text("atlas placeholder")
    labels.write_text("label placeholder")
    cli = workflow_cli_command(_state(run_classifier=True, run_trt=True, roi_atlas=str(atlas), roi_label_table=str(labels)))
    assert cli.startswith("hemispec workflow")
    assert '--input-glob "E:/data/**/*_GM_masked.nii.gz"' in cli
    assert f'--out-dir "{Path("E:/out/HemiSpec Run")}"' in cli
    assert f'--roi-atlas {atlas}' in cli
    assert f'--roi-label-table {labels}' in cli
    assert "--run-classifier" in cli
    assert "--run-trt" in cli


def test_gui_state_to_cli_command_no_roi_table() -> None:
    cli = workflow_cli_command(_state(export_roi_table=False, run_classifier=False))
    assert "--no-roi-table" in cli
    assert "--roi-atlas" not in cli
    assert "--roi-label-table" not in cli


def test_hidden_defaults_reach_workflow_config() -> None:
    config = make_workflow_config(_state(model_root="E:/models/dgn", gm_thresh=0.23, eps=1e-5))
    assert config.model_root == Path("E:/models/dgn")
    assert config.device == "auto"
    assert config.gm_thresh == 0.23
    assert config.eps == 1e-5


def test_gui_state_to_cli_command_quotes_shell_special_paths() -> None:
    cli_text = workflow_cli_command(_state(out_dir="E:/out/A&B", export_roi_table=False))
    assert f'--out-dir "{Path("E:/out/A&B")}"' in cli_text


def test_hidden_gui_defaults_match_cli_workflow_defaults() -> None:
    parser = cli.build_parser()
    args = parser.parse_args(["workflow", "--input-glob", "E:/data/*_GM_masked.nii.gz", "--out-dir", "E:/out"])
    config = make_workflow_config(_state(input_glob=args.input_glob, out_dir=args.out_dir, export_roi_table=not args.no_roi_table))

    assert config.device == args.device
    assert config.gm_thresh == args.gm_thresh
    assert config.eps == args.eps
    assert config.output_suffix == args.output_suffix
    assert config.reconstructed_suffix_to_strip == args.pred_suffix_to_strip
    assert config.actual_suffix_to_strip == args.actual_suffix_to_strip
    assert config.export_voxelwise is (not args.no_voxelwise)
    assert config.write_nan_outside is (not args.write_zero_outside)
    assert config.roi_stat == args.roi_stat
    assert config.classifier_mode == args.classifier_mode
    assert config.run_classifier is args.run_classifier
    assert config.run_trt is args.run_trt
    assert config.trt_file_regex == args.trt_file_regex
    assert config.trt_session_a == args.trt_session_a
    assert config.trt_session_b == args.trt_session_b
    assert config.trt_metric == args.trt_metric
    assert config.trt_mask_type == args.trt_mask_type
    assert config.trt_thr == args.trt_thr
    assert config.trt_rate_thr == args.trt_rate_thr
    assert config.trt_mask_mode == args.trt_mask_mode
    assert config.trt_symmetrize is (not args.trt_no_symmetrize)
    assert config.trt_write_plots is (not args.trt_no_plots)
    assert config.verbose_every == args.verbose_every


def test_runtime_asset_status_reports_model_enabled_setup(monkeypatch, tmp_path: Path) -> None:
    model_root = tmp_path / "models" / "dgn"
    (model_root / "outputs_bi_stable_L" / "ckpts").mkdir(parents=True)
    (model_root / "outputs_bi_stable_R" / "ckpts").mkdir(parents=True)
    (model_root / "outputs_bi_stable_L" / "ckpts" / "best_netG_R2L.pth").write_bytes(b"toy")
    (model_root / "outputs_bi_stable_R" / "ckpts" / "best_netG_L2R.pth").write_bytes(b"toy")

    atlas = tmp_path / "atlases" / "glasser.nii.gz"
    labels = tmp_path / "atlases" / "labels.xlsx"
    atlas.parent.mkdir(parents=True)
    atlas.write_bytes(b"atlas")
    labels.write_bytes(b"labels")

    classifier = tmp_path / "models" / "classifier"
    for metric in ("GLS_ANS", "GLS_RNS"):
        metric_dir = classifier / metric
        metric_dir.mkdir(parents=True)
        (metric_dir / f"{metric}_noICBM_train_ICBM_test_model_bundle.joblib").write_bytes(b"joblib")

    monkeypatch.setattr(gui_module, "_is_torch_available", lambda: True)

    statuses = build_runtime_asset_status(
        _state(
            model_root=str(model_root),
            roi_atlas=str(atlas),
            roi_label_table=str(labels),
            classifier_model_dir=str(classifier),
        )
    )
    by_key = {item.key: item for item in statuses}

    assert by_key["dgn"].ok is True
    assert by_key["atlas"].ok is True
    assert by_key["classifier"].ok is True
    assert by_key["torch"].ok is True
    assert runtime_mode_label(statuses) == "Model-enabled"


def test_runtime_asset_status_reports_lightweight_when_assets_missing(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(gui_module, "_is_torch_available", lambda: False)

    statuses = build_runtime_asset_status(
        _state(
            model_root=str(tmp_path / "missing-dgn"),
            roi_atlas=str(tmp_path / "missing-atlas.nii.gz"),
            roi_label_table=str(tmp_path / "missing-labels.xlsx"),
            classifier_model_dir=str(tmp_path / "missing-classifier"),
        )
    )
    by_key = {item.key: item for item in statuses}

    assert by_key["dgn"].ok is False
    assert "missing" in by_key["dgn"].message
    assert by_key["atlas"].ok is False
    assert by_key["classifier"].ok is False
    assert by_key["torch"].ok is False
    assert runtime_mode_label(statuses) == "Lightweight"


def test_runtime_mode_treats_classifier_as_optional(monkeypatch, tmp_path: Path) -> None:
    model_root = tmp_path / "models" / "dgn"
    (model_root / "outputs_bi_stable_L" / "ckpts").mkdir(parents=True)
    (model_root / "outputs_bi_stable_R" / "ckpts").mkdir(parents=True)
    (model_root / "outputs_bi_stable_L" / "ckpts" / "best_netG_R2L.pth").write_bytes(b"toy")
    (model_root / "outputs_bi_stable_R" / "ckpts" / "best_netG_L2R.pth").write_bytes(b"toy")
    atlas = tmp_path / "atlas.nii.gz"
    labels = tmp_path / "labels.xlsx"
    atlas.write_bytes(b"atlas")
    labels.write_bytes(b"labels")
    monkeypatch.setattr(gui_module, "_is_torch_available", lambda: True)

    statuses = build_runtime_asset_status(
        _state(
            model_root=str(model_root),
            roi_atlas=str(atlas),
            roi_label_table=str(labels),
            classifier_model_dir=str(tmp_path / "missing-classifier"),
        )
    )
    by_key = {item.key: item for item in statuses}

    assert by_key["classifier"].ok is False
    assert runtime_mode_label(statuses) == "Model-enabled"


def test_runtime_asset_status_reports_partial_dgn_bundle(monkeypatch, tmp_path: Path) -> None:
    model_root = tmp_path / "models" / "dgn"
    (model_root / "outputs_bi_stable_L" / "ckpts").mkdir(parents=True)
    (model_root / "outputs_bi_stable_L" / "ckpts" / "best_netG_R2L.pth").write_bytes(b"toy")
    monkeypatch.setattr(gui_module, "_is_torch_available", lambda: True)

    statuses = build_runtime_asset_status(_state(model_root=str(model_root)))
    dgn = {item.key: item for item in statuses}["dgn"]

    assert dgn.ok is False
    assert "partial/missing checkpoints" in dgn.message
    assert "L_to_R" in dgn.message


def test_runtime_asset_status_reports_partial_atlas(tmp_path: Path) -> None:
    atlas = tmp_path / "atlas.nii.gz"
    atlas.write_bytes(b"atlas")

    statuses = build_runtime_asset_status(
        _state(roi_atlas=str(atlas), roi_label_table=str(tmp_path / "missing-labels.xlsx"))
    )
    atlas_status = {item.key: item for item in statuses}["atlas"]

    assert atlas_status.ok is False
    assert atlas_status.message == "missing label table"
