import os
import sys
from pathlib import Path

import pytest

import hemispec.cli as cli
import hemispec.gui as gui_module
from hemispec.gui import (
    ENCAPSULATED_DEFAULTS,
    LOG_TAG_DEFAULT,
    LOG_TAG_ERROR,
    LOG_TAG_MODELS,
    LOG_TAG_SUCCESS,
    LOG_TAG_WARNING,
    LOG_TAG_WORKFLOW,
    WORKFLOW_ENCAPSULATED_FIELDS,
    WORKFLOW_REQUIRED_FIELDS,
    WORKFLOW_VISIBLE_FIELDS,
    HemiSpecGui,
    NoInputFilesError,
    ProgressUpdate,
    build_runtime_asset_status,
    classify_log_line,
    find_matching_inputs,
    fit_window_geometry,
    format_elapsed,
    format_percent,
    gui_icon_path,
    gui_theme_mark_path,
    make_workflow_config,
    match_count_display,
    output_dir_is_nonempty,
    parse_progress_line,
    parse_stage_line,
    preflight_workflow_state,
    runtime_mode_display,
    runtime_mode_label,
    runtime_status_display,
    safe_match_count,
    should_autoscroll,
    stage_detail_display,
    stage_display,
    status_line_text,
    status_stage_text,
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
        "keep_intermediate": False,
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
        "keep_intermediate",
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
    assert "--keep-intermediate" not in cli


def test_gui_state_to_cli_command_can_keep_intermediate() -> None:
    cli = workflow_cli_command(_state(export_roi_table=False, keep_intermediate=True))
    assert "--keep-intermediate" in cli


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
    assert config.keep_intermediate is args.keep_intermediate
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


def test_progress_parser_reads_inference_counter() -> None:
    update = parse_progress_line("[infer] L_to_R 3/12 done sub-001_GM_masked.nii.gz")
    assert update is not None
    assert update.stage == "l_to_r"
    assert update.current == 3
    assert update.total == 12
    assert update.fraction == 0.25
    assert "sub-001_GM_masked.nii.gz" in update.detail


def test_progress_parser_reads_workflow_stage_and_merge_counter() -> None:
    stage = parse_stage_line("[workflow] Running R_to_L inference and metrics")
    merge = parse_progress_line("[merge] 2/5 sub-002")

    assert stage is not None
    assert stage.stage == "r_to_l"
    assert merge is not None
    assert merge.stage == "merge"
    assert merge.current == 2
    assert merge.total == 5
    assert merge.fraction == 0.4
    assert parse_progress_line("ordinary output line") is None


def test_stage_display_is_bilingual() -> None:
    assert stage_display("classifier", "en") == "Classifier validation"
    assert stage_display("classifier", "zh") == "分类器验证"


def test_find_matching_inputs_is_recursive_and_file_only(tmp_path: Path) -> None:
    nested = tmp_path / "sub-001" / "derivatives"
    nested.mkdir(parents=True)
    first = nested / "sub-001_GM_masked.nii.gz"
    first.write_bytes(b"nifti")
    (nested / "notes.txt").write_text("not an input")

    matches = find_matching_inputs(str(tmp_path / "**" / "*_GM_masked.nii.gz"))

    assert matches == (first,)


def test_output_dir_is_nonempty_only_for_existing_entries(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    full = tmp_path / "full"
    full.mkdir()
    (full / "existing.txt").write_text("keep me")

    assert output_dir_is_nonempty(empty) is False
    assert output_dir_is_nonempty(full) is True
    assert output_dir_is_nonempty(tmp_path / "missing") is False


def test_preflight_requires_matched_inputs(tmp_path: Path) -> None:
    with pytest.raises(NoInputFilesError) as excinfo:
        preflight_workflow_state(
            _state(input_glob=str(tmp_path / "*_GM_masked.nii.gz"), out_dir=str(tmp_path / "out"))
        )

    # Missing inputs stay blocking (spec 7.3 "No inputs" error dialog).
    assert excinfo.value.input_glob.endswith("*_GM_masked.nii.gz")


def test_preflight_requires_confirmation_for_nonempty_output(tmp_path: Path) -> None:
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    first = inputs / "sub-001_GM_masked.nii.gz"
    first.write_bytes(b"nifti")
    out = tmp_path / "out"
    out.mkdir()
    (out / "old.txt").write_text("old")

    # Spec 7.3 changed this from a hard rejection to an overwrite confirmation.
    result = preflight_workflow_state(_state(input_glob=str(inputs), out_dir=str(out)))

    assert result.matches == (first,)
    assert result.requires_confirmation is True


def test_preflight_accepts_matched_inputs_and_empty_output(tmp_path: Path) -> None:
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    first = inputs / "sub-001_GM_masked.nii.gz"
    first.write_bytes(b"nifti")
    out = tmp_path / "out"
    out.mkdir()

    result = preflight_workflow_state(_state(input_glob=str(inputs), out_dir=str(out)))

    assert result.matches == (first,)
    assert result.requires_confirmation is False


def test_gui_icon_assets_resolve_from_package() -> None:
    assert gui_icon_path("hemispec.png") is not None
    assert gui_icon_path("hemispec.ico") is not None
    assert gui_icon_path("does-not-exist.png") is None


def test_window_geometry_fits_200_percent_work_area() -> None:
    # Spec 7.1: 2560x1360 physical at 200% is 1280x680 logical. The target is
    # min(1240, 0.94*1280=1203) x min(800, 0.92*680=625), so both dimensions
    # changed from the earlier fixed 1240x584 clamp.
    width, height, x, y, min_width, min_height = fit_window_geometry((0, 0, 2560, 1360), 2.0)

    assert (width, height) == (1203, 625)
    # minsize is the spec formula min(900, 1280-32) x min(560, 680-32).
    assert (min_width, min_height) == (900, 560)
    assert min_width <= width
    assert min_height <= height
    assert x >= 0 and y >= 0
    assert x + round(width * 2.0) <= 2560
    assert y + round(height * 2.0) <= 1360


def test_window_geometry_clamps_to_small_work_area() -> None:
    # 1280x680 physical at 200% is 640x340 logical: target 601x312, and the
    # spec minsize min(900, 608)=608 x min(560, 308)=308 raises the width.
    width, height, x, y, min_width, min_height = fit_window_geometry((0, 0, 1280, 680), 2.0)

    assert (width, height) == (608, 312)
    assert (min_width, min_height) == (608, 308)
    assert min_width <= width
    assert min_height <= height
    assert x + round(width * 2.0) <= 1280
    assert y + round(height * 2.0) <= 680


def test_window_minsize_allows_single_column_layout_at_100_and_200_percent() -> None:
    # Spec 7.1/7.2: minsize width min(900, workW-32) must stay below the 1060
    # logical breakpoint so the single-column layout is reachable by resizing.
    from hemispec.gui import RESPONSIVE_BREAKPOINT

    for scaling in (1.0, 2.0):
        width, height, _x, _y, min_width, min_height = fit_window_geometry(
            (0, 0, 1920, 1080), scaling
        )
        assert min_width == 900
        assert min_width < RESPONSIVE_BREAKPOINT
        # At 200% the logical work height is 540, so the spec formula gives
        # min(560, 540-32) = 508; at 100% it is the full 560.
        assert min_height == (560 if scaling == 1.0 else 508)
        assert min_width <= width and min_height <= height


def test_window_default_size_matches_spec_caps() -> None:
    # Spec 7.1: target logical size caps at 1240 x 800.
    from hemispec.gui import DEFAULT_WINDOW_SIZE

    assert DEFAULT_WINDOW_SIZE == (1240, 800)
    width, height, _x, _y, _min_w, _min_h = fit_window_geometry((0, 0, 3840, 2160), 1.0)
    assert (width, height) == (1240, 800)


def test_runtime_display_translates_mode_status_and_guidance(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(gui_module, "_is_torch_available", lambda: False)
    statuses = build_runtime_asset_status(
        _state(
            model_root=str(tmp_path / "missing-dgn"),
            roi_atlas=str(tmp_path / "missing-atlas.nii.gz"),
            roi_label_table=str(tmp_path / "missing-labels.xlsx"),
            classifier_model_dir=str(tmp_path / "missing-classifier"),
        )
    )
    dgn = {item.key: item for item in statuses}["dgn"]

    assert runtime_mode_label(statuses) == "Lightweight"
    assert runtime_mode_display("Lightweight", "zh") == "轻量模式"
    assert runtime_mode_display("Model-enabled", "zh") == "完整模型"
    assert runtime_status_display(dgn, "en") == (dgn.message, dgn.guidance)
    assert runtime_status_display(dgn, "zh")[0] == "模型根目录缺失/未下载"
    assert "默认安装" in runtime_status_display(dgn, "zh")[1]


def test_stage_detail_display_translates_prefix_only() -> None:
    assert stage_detail_display("done sub-001_GM_masked.nii.gz", "zh") == "完成 sub-001_GM_masked.nii.gz"
    assert stage_detail_display("done sub-001_GM_masked.nii.gz", "en") == "done sub-001_GM_masked.nii.gz"


def test_status_line_formats_stage_counts_percent_and_clock() -> None:
    # Spec section 7.2: "R→L 12/24" on the left and "50% · 03:12" on the right.
    left, right = status_line_text("r_to_l", 12, 24, 0.5, 192, "en")
    assert left == "R→L 12/24"
    assert right == "50% · 03:12"

    assert status_stage_text("l_to_r", 3, 12, "zh") == "左→右 3/12"
    assert status_stage_text("merge", None, None, "en") == "Merge"
    assert status_stage_text("summary", None, None, "zh") == "汇总"


def test_status_line_uses_spec_validation_copy() -> None:
    assert status_stage_text("classifier", None, None, "en") == "Validating classifier…"
    assert status_stage_text("classifier", None, None, "zh") == "正在验证分类器…"
    assert (
        status_stage_text("trt", None, None, "en")
        == "Validating test–retest reliability…"
    )
    assert status_stage_text("trt", None, None, "zh") == "正在验证重测信度…"


def test_clock_and_percent_formatting() -> None:
    assert format_elapsed(0) == "00:00"
    assert format_elapsed(72.9) == "01:12"
    assert format_elapsed(3600) == "60:00"
    assert format_elapsed(-5) == "00:00"
    assert format_percent(None) == "0%"
    assert format_percent(0.504) == "50%"
    assert format_percent(1.0) == "100%"
    assert format_percent(2.0) == "100%"


def test_match_count_display_is_bilingual_and_colored() -> None:
    assert match_count_display(24, "en") == ("24 files found", "#276B43")
    assert match_count_display(24, "zh") == ("找到 24 个文件", "#276B43")
    assert match_count_display(0, "en") == ("No matching files", "#84251D")
    assert match_count_display(None, "zh") == ("没有匹配的文件", "#84251D")


def test_safe_match_count_counts_fake_gm_files(tmp_path: Path) -> None:
    # Fake inputs live in tmp_path, never in the repository.
    for index in range(3):
        (tmp_path / f"sub-{index:03d}_GM_masked.nii.gz").write_bytes(b"nifti")
    (tmp_path / "notes.txt").write_text("ignored")

    assert safe_match_count(str(tmp_path / "*_GM_masked.nii.gz")) == 3
    assert safe_match_count(str(tmp_path / "empty-dir" / "*_GM_masked.nii.gz")) == 0


def test_autoscroll_only_when_already_at_bottom() -> None:
    assert should_autoscroll((0.0, 1.0)) is True
    assert should_autoscroll((0.5, 0.9)) is False
    assert should_autoscroll((0.0, 0.995)) is True
    assert should_autoscroll((0.0, 0.0)) is False


def test_classify_log_line_matches_spec_table() -> None:
    # Spec 7.3 "Log tags": one row per line, matched top to bottom.
    assert classify_log_line("[workflow] Running L_to_R inference and metrics\n") == LOG_TAG_WORKFLOW
    assert classify_log_line("[models] downloading asset -> target\n") == LOG_TAG_MODELS
    assert classify_log_line("[warning] ROI atlas not found\n") == LOG_TAG_WARNING
    assert classify_log_line("WARNING: low memory\n") == LOG_TAG_WARNING
    assert classify_log_line("[error] RuntimeError: boom\n") == LOG_TAG_ERROR
    assert classify_log_line("Traceback (most recent call last):\n") == LOG_TAG_ERROR
    assert classify_log_line("[done] HemiSpec workflow complete\n") == LOG_TAG_SUCCESS
    assert classify_log_line("out_dir: E:/out\n") == LOG_TAG_DEFAULT
    # Partial lines (no trailing newline) still classify.
    assert classify_log_line("[models] downloading") == LOG_TAG_MODELS
    # Spec table order wins when a line matches several rows.
    assert classify_log_line("[workflow] ERROR while merging\n") == LOG_TAG_WORKFLOW


# ---------------------------------------------------------------- GUI behavior
# These instantiate the real window, so they only run where Tk is available.

GUI_REQUIRES_DISPLAY = pytest.mark.skipif(
    not (
        sys.platform.startswith("win")
        or os.environ.get("DISPLAY")
        or os.environ.get("WAYLAND_DISPLAY")
    ),
    reason="Tk GUI tests require a graphical display",
)


def _make_gui() -> HemiSpecGui:
    # PIL ImageTk binds a PhotoImage to one Tk interpreter; a header image made
    # for a destroyed interpreter breaks the next window. The tests exercise
    # widgets, not the logo, so use the spec's "H" mark fallback instead.
    original = HemiSpecGui._load_header_image
    HemiSpecGui._load_header_image = lambda self: None  # type: ignore[method-assign]
    try:
        app = HemiSpecGui()
    finally:
        HemiSpecGui._load_header_image = original  # type: ignore[method-assign]
    app.withdraw()
    # Pin English so assertions are independent of the host UI locale.
    app.language_var.set("en")
    app._apply_language()
    return app


@pytest.mark.gui
@GUI_REQUIRES_DISPLAY
def test_run_continues_after_overwrite_confirmation(tmp_path: Path, monkeypatch) -> None:
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    (inputs / "sub-001_GM_masked.nii.gz").write_bytes(b"nifti")
    out = tmp_path / "out"
    out.mkdir()
    (out / "old.txt").write_text("old")

    asked: list[str] = []

    def fake_askokcancel(title: str, message: str, **kwargs: object) -> bool:
        asked.append(title)
        return True

    started: list[object] = []

    class FakeThread:
        def __init__(self, target: object, args: tuple[object, ...], daemon: bool) -> None:
            self._args = args

        def start(self) -> None:
            started.append(self._args[0])

    monkeypatch.setattr(gui_module.messagebox, "askokcancel", fake_askokcancel)
    monkeypatch.setattr(gui_module.threading, "Thread", FakeThread)
    app = _make_gui()
    try:
        app.vars["input_glob"].set(str(inputs / "*_GM_masked.nii.gz"))
        app.vars["out_dir"].set(str(out))
        app._run_clicked()
        # Confirm was asked once and the workflow was actually started.
        assert asked and "not empty" in asked[0]
        assert started
        assert app.is_running is True
    finally:
        app.is_running = False
        app.destroy()


@pytest.mark.gui
@GUI_REQUIRES_DISPLAY
def test_run_cancelled_at_overwrite_confirmation_does_not_start(
    tmp_path: Path, monkeypatch
) -> None:
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    (inputs / "sub-001_GM_masked.nii.gz").write_bytes(b"nifti")
    out = tmp_path / "out"
    out.mkdir()
    (out / "old.txt").write_text("old")

    started: list[object] = []

    class FakeThread:
        def __init__(self, target: object, args: tuple[object, ...], daemon: bool) -> None:
            self._args = args

        def start(self) -> None:
            started.append(self._args[0])

    monkeypatch.setattr(gui_module.messagebox, "askokcancel", lambda *a, **k: False)
    monkeypatch.setattr(gui_module.threading, "Thread", FakeThread)
    app = _make_gui()
    try:
        app.vars["input_glob"].set(str(inputs / "*_GM_masked.nii.gz"))
        app.vars["out_dir"].set(str(out))
        app._run_clicked()
        assert not started
        assert app.is_running is False
    finally:
        app.destroy()


@pytest.mark.gui
@GUI_REQUIRES_DISPLAY
def test_missing_inputs_still_blocks_run(tmp_path: Path, monkeypatch) -> None:
    errors: list[str] = []
    started: list[object] = []

    class FakeThread:
        def __init__(self, target: object, args: tuple[object, ...], daemon: bool) -> None:
            self._args = args

        def start(self) -> None:
            started.append(self._args[0])

    monkeypatch.setattr(
        gui_module.messagebox, "showerror", lambda title, message, **k: errors.append(message)
    )
    monkeypatch.setattr(gui_module.threading, "Thread", FakeThread)
    app = _make_gui()
    try:
        app.vars["input_glob"].set(str(tmp_path / "nothing" / "*_GM_masked.nii.gz"))
        app.vars["out_dir"].set(str(tmp_path / "out"))
        app._run_clicked()
        assert errors and "No input files match" in errors[0]
        assert not started
    finally:
        app.destroy()


@pytest.mark.gui
@GUI_REQUIRES_DISPLAY
def test_failure_shows_status_line_without_modal(monkeypatch) -> None:
    shown: list[str] = []
    monkeypatch.setattr(
        gui_module.messagebox, "showerror", lambda *a, **k: shown.append("error")
    )
    monkeypatch.setattr(
        gui_module.messagebox, "showinfo", lambda *a, **k: shown.append("info")
    )
    monkeypatch.setattr(
        gui_module.messagebox, "showwarning", lambda *a, **k: shown.append("warning")
    )
    app = _make_gui()
    try:
        app.is_running = True
        app._run_finished(None, (RuntimeError("boom"), "Traceback: boom"))
        # Spec 7.3: no modal; status line and stepper report the failure.
        assert shown == []
        assert app.run_stage_label.cget("text") == "Run failed — see log"
        assert app.stepper.node_state("l_to_r") == "error"
        assert "boom" in app.log_box.get("1.0", "end-1c")
    finally:
        app.destroy()


@pytest.mark.gui
@GUI_REQUIRES_DISPLAY
def test_status_line_updates_from_progress(monkeypatch) -> None:
    app = _make_gui()
    try:
        app._run_started_at = 0.0
        app._run_fraction = 0.0
        monkeypatch.setattr(app, "_elapsed_seconds", lambda: 192.0)
        app._apply_progress(ProgressUpdate(stage="r_to_l", current=12, total=24))
        assert app.run_stage_label.cget("text") == "R→L 12/24"
        assert app.run_elapsed_label.cget("text") == "50% · 03:12"
    finally:
        app.destroy()


@pytest.mark.gui
@GUI_REQUIRES_DISPLAY
def test_copy_feedback_reverts_after_delay(monkeypatch) -> None:
    app = _make_gui()
    try:
        monkeypatch.setattr(app, "clipboard_clear", lambda: None)
        monkeypatch.setattr(app, "clipboard_append", lambda text: None)
        app._copy_cli()
        assert app.copy_button.cget("text") == "Copied ✓"
        # Simulate the 1.5s timer firing.
        app._revert_copy_feedback()
        assert app.copy_button.cget("text") == "Copy"
    finally:
        app.destroy()


@pytest.mark.gui
@GUI_REQUIRES_DISPLAY
def test_log_does_not_autoscroll_while_scrolled_up(monkeypatch) -> None:
    app = _make_gui()
    try:
        seen: list[str] = []
        monkeypatch.setattr(app.log_box, "see", lambda index: seen.append(index))
        monkeypatch.setattr(app, "_log_is_at_bottom", lambda: False)
        app._log("more output\n")
        assert seen == []
        monkeypatch.setattr(app, "_log_is_at_bottom", lambda: True)
        app._log("more output\n")
        assert seen == ["end"]
    finally:
        app.destroy()


@pytest.mark.gui
@GUI_REQUIRES_DISPLAY
def test_log_tags_exist_and_are_applied_per_line() -> None:
    # Spec 7.3 "Log tags": tags exist with the spec colors and every line of a
    # mixed multi-line chunk gets its own tag.
    app = _make_gui()
    try:
        textbox = app.log_box._textbox
        configured = set(textbox.tag_names())
        assert {
            LOG_TAG_DEFAULT,
            LOG_TAG_WORKFLOW,
            LOG_TAG_MODELS,
            LOG_TAG_WARNING,
            LOG_TAG_ERROR,
            LOG_TAG_SUCCESS,
        }.issubset(configured)
        assert textbox.tag_cget(LOG_TAG_WORKFLOW, "foreground") == "#0A5957"
        assert textbox.tag_cget(LOG_TAG_MODELS, "foreground") == "#0D6F6D"
        assert textbox.tag_cget(LOG_TAG_WARNING, "foreground") == "#8A5508"
        assert textbox.tag_cget(LOG_TAG_ERROR, "foreground") == "#84251D"
        assert textbox.tag_cget(LOG_TAG_SUCCESS, "foreground") == "#276B43"
        assert textbox.tag_cget(LOG_TAG_DEFAULT, "foreground") == "#323B3D"
        assert textbox.tag_cget(LOG_TAG_WORKFLOW, "font")
        assert textbox.tag_cget(LOG_TAG_SUCCESS, "font")

        app._clear_log()
        app._log(
            "[workflow] Running L_to_R inference and metrics\n"
            "[models] downloading asset\n"
            "[warning] ROI atlas not found\n"
            "[error] RuntimeError: boom\n"
            "[done] HemiSpec workflow complete\n"
            "out_dir: E:/out\n"
        )
        for line_number, tag in enumerate(
            (
                LOG_TAG_WORKFLOW,
                LOG_TAG_MODELS,
                LOG_TAG_WARNING,
                LOG_TAG_ERROR,
                LOG_TAG_SUCCESS,
                LOG_TAG_DEFAULT,
            ),
            start=1,
        ):
            assert textbox.tag_names(f"{line_number}.0")[0] == tag
    finally:
        app.destroy()


@pytest.mark.gui
@GUI_REQUIRES_DISPLAY
def test_progress_is_indeterminate_at_startup_and_on_model_download() -> None:
    # Spec 7.3: indeterminate during model download or startup; the first
    # determinate counter update stops the animation.
    app = _make_gui()
    try:
        app._set_progress_indeterminate()
        assert app.progress_bar._mode == "indeterminate"
        assert app.progress_bar._loop_running is True
        app._handle_output_text("[models] downloading asset -> target\n")
        assert app.progress_bar._mode == "indeterminate"
        app._handle_output_text("[infer] L_to_R 1/8 start sub-001\n")
        assert app.progress_bar._mode == "determinate"
        assert app.progress_bar._loop_running is False
        assert app.progress_bar._determinate_value == pytest.approx(0.125)
        # Finish stops the animation and shows the terminal fraction.
        app._set_progress_indeterminate()
        app._finish_progress(1.0, "stage_idle")
        assert app.progress_bar._mode == "determinate"
        assert app.progress_bar._loop_running is False
        assert app.progress_bar._determinate_value == pytest.approx(1.0)
    finally:
        app.destroy()


@pytest.mark.gui
@GUI_REQUIRES_DISPLAY
def test_action_buttons_are_keyboard_reachable() -> None:
    # Spec 7.5: every action is keyboard-reachable, and disabled buttons
    # ignore Return/Space.
    app = _make_gui()
    try:
        buttons = (
            app.run_button,
            app.stop_button,
            app.input_browse_button,
            app.output_browse_button,
            app.open_button,
            app.copy_button,
            app.refresh_button,
            app.log_copy_button,
            app.log_open_button,
            app.clear_button,
            app._language_buttons["zh"],
            app._language_buttons["en"],
        )
        for button in buttons:
            assert str(button._canvas.cget("takefocus")) == "1"
            assert button._canvas.bind("<Return>")
            assert button._canvas.bind("<KP_Enter>")
            assert button._canvas.bind("<space>")

        # The bound handler invokes the command; disabled buttons do nothing.
        calls: list[str] = []
        app.run_button.configure(command=lambda: calls.append("run"))
        handler = getattr(app.run_button, "_hemispec_keyboard_invoke")
        handler()
        assert calls == ["run"]

        app.run_button.configure(state="disabled")
        handler()
        assert calls == ["run"]
        app.run_button.configure(state="normal")

        app.stop_button.configure(command=lambda: calls.append("stop"))
        app.stop_button.configure(state="disabled")
        getattr(app.stop_button, "_hemispec_keyboard_invoke")()
        assert "stop" not in calls
        app.stop_button.configure(state="normal")
        getattr(app.stop_button, "_hemispec_keyboard_invoke")()
        assert "stop" in calls
    finally:
        app.destroy()


@pytest.mark.gui
@GUI_REQUIRES_DISPLAY
def test_output_row_and_log_toolbar_button_copy() -> None:
    # Spec 7.2/7.4: the output row says "Open"/"打开"; the log toolbar keeps
    # "Open output"/"打开输出".
    app = _make_gui()
    try:
        assert app.open_button.cget("text") == "Open"
        assert app.log_open_button.cget("text") == "Open output"
        app.language_var.set("zh")
        app._apply_language()
        assert app.open_button.cget("text") == "打开"
        assert app.log_open_button.cget("text") == "打开输出"
    finally:
        app.destroy()

_THEME_META_FIELDS = {"id", "name_en", "name_zh", "appearance"}


def _theme_color_fields():
    import dataclasses

    from hemispec import gui as g

    return [f.name for f in dataclasses.fields(g.Theme) if f.name not in _THEME_META_FIELDS]


def test_default_theme_is_cool_teal():
    from hemispec import gui as g

    assert g.DEFAULT_THEME == "cool_teal"
    assert g.DEFAULT_THEME in g.THEMES


def test_theme_colors_are_hex():
    import re

    from hemispec import gui as g

    for theme in g.THEMES.values():
        for name in _theme_color_fields():
            assert re.fullmatch(r"#[0-9A-Fa-f]{6}", getattr(theme, name)), (theme.id, name)


def test_module_color_constants_mirror_default_theme():
    from hemispec import gui as g

    theme = g.THEMES["cool_teal"]
    mirrored = [n for n in _theme_color_fields() if n not in {"danger_text", "highlight"}]
    assert mirrored
    for name in mirrored:
        assert getattr(g, name.upper()) == getattr(theme, name), name


def test_hex_literals_only_in_theme_registry():
    import re
    from pathlib import Path

    from hemispec import gui as g

    lines = Path(g.__file__).read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if "THEME_COOL_TEAL = Theme(" in line)
    end = next(i for i, line in enumerate(lines) if line.startswith("THEMES: dict[str, Theme]"))
    for i, line in enumerate(lines):
        if re.search(r"#[0-9A-Fa-f]{6}\b", line):
            assert start < i < end, (i + 1, line)
_THEME_TEXT_PAIRS = [
    (fg, bg)
    for fg in ("ink_900", "ink_700", "ink_600", "ink_500")
    for bg in ("paper_0", "paper_50", "paper_100", "log_bg")
] + [
    ("paper_0", "teal_600"),
    ("teal_700", "teal_50"),
    ("teal_700", "paper_0"),
    ("teal_700", "log_bg"),
    ("teal_600", "log_bg"),
    ("warning_fg", "log_bg"),
    ("verm_700", "log_bg"),
    ("success_fg", "log_bg"),
    ("verm_600", "paper_0"),
    ("danger_text", "paper_0"),
    ("success_fg", "paper_0"),
    ("verm_700", "paper_0"),
    ("success_fg", "success_bg"),
    ("warning_fg", "warning_bg"),
    ("ink_600", "paper_200"),
]
# Status dots (success/warning/verm accents) are exempt: they are always paired with a word.
_THEME_MARK_PAIRS = [(mark, "paper_0") for mark in ("line_400", "control_off", "teal_500", "highlight")]


def _contrast_ratio(a, b):
    def luminance(hex_color):
        channels = []
        for i in (1, 3, 5):
            c = int(hex_color[i : i + 2], 16) / 255
            channels.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
        return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]

    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_all_four_themes_registered():
    from hemispec import gui as g

    assert list(g.THEMES) == ["cool_teal", "cool_cyan", "ink_night", "graphite_bronze"]
    names = {tid: (t.name_en, t.name_zh, t.appearance) for tid, t in g.THEMES.items()}
    assert names == {
        "cool_teal": ("Cool Teal", "冷白·青", "light"),
        "cool_cyan": ("Cool Cyan", "冷白·电青", "light"),
        "ink_night": ("Ink Night", "墨夜·青朱", "dark"),
        "graphite_bronze": ("Graphite Bronze", "石墨·青铜", "dark"),
    }


def test_theme_text_contrast():
    from hemispec import gui as g

    failures = [
        (tid, fg, bg, round(_contrast_ratio(getattr(t, fg), getattr(t, bg)), 2))
        for tid, t in g.THEMES.items()
        for fg, bg in _THEME_TEXT_PAIRS
        if _contrast_ratio(getattr(t, fg), getattr(t, bg)) < 4.5
    ]
    assert not failures


def test_theme_mark_contrast():
    from hemispec import gui as g

    failures = [
        (tid, mark, bg, round(_contrast_ratio(getattr(t, mark), getattr(t, bg)), 2))
        for tid, t in g.THEMES.items()
        for mark, bg in _THEME_MARK_PAIRS
        if _contrast_ratio(getattr(t, mark), getattr(t, bg)) < 3.0
    ]
    assert not failures


# --------------------------------------------------------------- theme runtime
COOL_TEAL_ONLY_COLORS = {"#F6F8F8", "#FAFBFB", "#EEF2F2", "#E4EAEA"}


def _iter_widget_colors(widget):
    """Yield every fg_color / border_color / text_color value in the tree."""

    stack = [widget]
    while stack:
        current = stack.pop()
        for attribute in ("fg_color", "border_color", "text_color"):
            try:
                value = current.cget(attribute)
            except Exception:
                continue
            if isinstance(value, str) and value.startswith("#"):
                yield attribute, value.upper()
        try:
            children = current.winfo_children()
        except Exception:
            children = []
        stack.extend(children)


@pytest.fixture
def _restore_default_theme():
    yield
    gui_module.apply_theme_globals("cool_teal")


@pytest.mark.gui
@GUI_REQUIRES_DISPLAY
def test_theme_control_in_header_with_four_options(_restore_default_theme) -> None:
    app = _make_gui()
    try:
        assert app.theme_var.get() == "cool_teal"
        assert list(app.theme_option.cget("values")) == [
            "Cool Teal",
            "Cool Cyan",
            "Ink Night",
            "Graphite Bronze",
        ]
        assert app.theme_label.cget("text") == "Theme"
        app.language_var.set("zh")
        app._apply_language()
        assert list(app.theme_option.cget("values")) == [
            "冷白·青",
            "冷白·电青",
            "墨夜·青朱",
            "石墨·青铜",
        ]
        assert app.theme_label.cget("text") == "主题"
    finally:
        app.destroy()


@pytest.mark.gui
@GUI_REQUIRES_DISPLAY
def test_apply_theme_recolors_widgets_and_restores(_restore_default_theme) -> None:
    app = _make_gui()
    try:
        cool_window = app.cget("fg_color")
        assert cool_window == "#F6F8F8"
        assert app.log_box.cget("fg_color") == "#FAFBFB"
        assert app._cards["input_output"].cget("fg_color") == "#FFFFFF"

        assert app.apply_theme("ink_night") is True
        assert app.theme_var.get() == "ink_night"
        assert app.cget("fg_color") == "#0B1015"
        assert app._cards["input_output"].cget("fg_color") == "#121A21"
        assert app.log_box.cget("fg_color") == "#0E151B"

        stray = {
            (attribute, value)
            for attribute, value in _iter_widget_colors(app)
            if value in COOL_TEAL_ONLY_COLORS
        }
        assert not stray, stray

        assert app.apply_theme("cool_teal") is True
        assert app.cget("fg_color") == "#F6F8F8"
        assert app._cards["input_output"].cget("fg_color") == "#FFFFFF"
    finally:
        app.destroy()


@pytest.mark.gui
@GUI_REQUIRES_DISPLAY
def test_apply_theme_preserves_state(_restore_default_theme) -> None:
    app = _make_gui()
    try:
        app.vars["input_glob"].set("Z:/data/*_GM_masked.nii.gz")
        app.vars["run_classifier"].set(True)
        app._log("[workflow] keep me across themes\n")
        before = app.log_box.get("1.0", "end-1c")

        assert app.apply_theme("graphite_bronze") is True

        assert app.vars["input_glob"].get() == "Z:/data/*_GM_masked.nii.gz"
        assert app.vars["run_classifier"].get() is True
        after = app.log_box.get("1.0", "end-1c")
        assert after == before
    finally:
        app.destroy()


@pytest.mark.gui
@GUI_REQUIRES_DISPLAY
def test_apply_theme_refused_while_running(_restore_default_theme) -> None:
    app = _make_gui()
    try:
        app.is_running = True
        assert app.apply_theme("ink_night") is False
        assert app.theme_var.get() == "cool_teal"
        assert app.cget("fg_color") == "#F6F8F8"
        assert str(app.theme_option.cget("state")) == "disabled"

        app.is_running = False
        app._refresh_action_buttons()
        assert str(app.theme_option.cget("state")) == "normal"
    finally:
        app.destroy()


@pytest.mark.gui
@GUI_REQUIRES_DISPLAY
def test_theme_option_menu_keyboard_reachable(_restore_default_theme) -> None:
    app = _make_gui()
    try:
        canvas = app.theme_option._canvas
        assert str(canvas.cget("takefocus")) == "1"
        assert canvas.bind("<Return>")
        assert canvas.bind("<KP_Enter>")
        assert canvas.bind("<space>")
    finally:
        app.destroy()



@pytest.mark.gui
@GUI_REQUIRES_DISPLAY
def test_new_gui_reapplies_default_theme_globals(_restore_default_theme) -> None:
    """A fresh HemiSpecGui must reset the module color constants.

    Regression: __init__ only set the appearance mode, so after switching to
    ink_night in the same process a second window kept the dark constants even
    though theme_var said cool_teal.
    """

    first = _make_gui()
    try:
        assert first.apply_theme("ink_night") is True
        assert first.theme_var.get() == "ink_night"
    finally:
        first.destroy()

    second = _make_gui()
    try:
        assert gui_module.PAPER_50 == "#F6F8F8"
        assert second.cget("fg_color") == "#F6F8F8"
        assert second.theme_var.get() == "cool_teal"
    finally:
        second.destroy()


def test_theme_mark_files_cover_every_theme_with_distinct_transparent_pngs() -> None:
    pytest.importorskip("PIL")
    from PIL import Image

    assert set(gui_module.THEME_MARK_FILES) == set(gui_module.THEMES)
    seen: set[bytes] = set()
    for theme_id in gui_module.THEMES:
        path = gui_theme_mark_path(theme_id)
        assert path is not None and path.is_file(), theme_id
        with Image.open(path) as opened:
            assert opened.format == "PNG"
            assert opened.size == (256, 256)
            assert opened.mode == "RGBA"
            width, height = opened.size
            for corner in ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)):
                assert opened.getpixel(corner)[3] == 0, (theme_id, corner)
        seen.add(path.read_bytes())
    assert len(seen) == len(gui_module.THEMES)
    assert gui_theme_mark_path("no-such-theme") is None


def _make_gui_with_header_mark(monkeypatch) -> HemiSpecGui:
    # Load the real mark to record its path, but discard the CTkImage so no
    # PhotoImage is bound to this test's Tk interpreter.
    original = HemiSpecGui._load_header_image

    def load_and_discard(self):
        original(self)
        return None

    monkeypatch.setattr(HemiSpecGui, "_load_header_image", load_and_discard)
    app = HemiSpecGui()
    app.withdraw()
    return app


@pytest.mark.gui
@GUI_REQUIRES_DISPLAY
def test_header_mark_follows_active_theme(_restore_default_theme, monkeypatch) -> None:
    app = _make_gui_with_header_mark(monkeypatch)
    try:
        assert app._header_mark_path == gui_theme_mark_path("cool_teal")
        assert app.apply_theme("ink_night") is True
        assert app._header_mark_path == gui_theme_mark_path("ink_night")
        assert app.apply_theme("graphite_bronze") is True
        assert app._header_mark_path == gui_theme_mark_path("graphite_bronze")
    finally:
        app.destroy()


@pytest.mark.gui
@GUI_REQUIRES_DISPLAY
def test_window_icon_ignores_theme_marks(_restore_default_theme, monkeypatch) -> None:
    requested: list[str] = []
    real = gui_module.gui_icon_path

    def recording(filename: str = "hemispec.png"):
        requested.append(filename)
        return real(filename)

    app = _make_gui()
    try:
        monkeypatch.setattr(gui_module, "gui_icon_path", recording)
        for theme_id in ("cool_teal", "ink_night", "graphite_bronze"):
            assert app.apply_theme(theme_id) is True
            requested.clear()
            gui_module._apply_window_icon(app)
            assert requested and set(requested) <= {"hemispec.ico", "hemispec.png"}
        assert gui_icon_path("hemispec.png") is not None
        assert gui_icon_path("hemispec.ico") is not None
    finally:
        app.destroy()
