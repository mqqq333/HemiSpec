from hemispec.cli import build_parser


WORKFLOW_MINIMAL_ARGS = [
    "workflow",
    "--input-glob",
    "derivatives/*_GM_masked.nii.gz",
    "--out-dir",
    "outputs/hemispec_workflow",
]


def test_workflow_cli_defaults_match_standard_ans_rns_generator() -> None:
    args = build_parser().parse_args(WORKFLOW_MINIMAL_ARGS)
    assert args.no_roi_table is False
    assert args.run_classifier is False
    assert args.run_trt is False


def test_workflow_cli_roi_and_classifier_are_explicit_options() -> None:
    args = build_parser().parse_args(WORKFLOW_MINIMAL_ARGS + ["--no-roi-table"])
    assert args.no_roi_table is True
    assert args.run_classifier is False

    args = build_parser().parse_args(WORKFLOW_MINIMAL_ARGS + ["--run-classifier"])
    assert args.no_roi_table is False
    assert args.run_classifier is True
