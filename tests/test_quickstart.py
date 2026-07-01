from pathlib import Path

from hemispec.cli import build_parser, cmd_quickstart
from hemispec.quickstart import run_synthetic_quickstart


def test_synthetic_quickstart_runs_from_package(tmp_path: Path) -> None:
    result = run_synthetic_quickstart(tmp_path / "quickstart", n_subjects=2)

    assert result["n_pairs"] == 2
    assert (tmp_path / "quickstart" / "outputs" / "compute" / "ANS_group_masked_mean.nii.gz").exists()
    assert (tmp_path / "quickstart" / "outputs" / "compute" / "RNS_group_masked_mean.nii.gz").exists()
    assert (tmp_path / "quickstart" / "outputs" / "compute" / "toy_roi_summary.csv").exists()


def test_quickstart_cli_contract(tmp_path: Path, capsys) -> None:
    args = build_parser().parse_args(
        [
            "quickstart",
            "--out-dir",
            str(tmp_path / "cli_quickstart"),
            "--n-subjects",
            "1",
        ]
    )
    cmd_quickstart(args)

    captured = capsys.readouterr()
    assert "synthetic HemiSpec quickstart complete" in captured.out
    assert (tmp_path / "cli_quickstart" / "outputs" / "compute" / "toy_roi_summary.csv").exists()


def test_synthetic_quickstart_force_clears_stale_outputs(tmp_path: Path) -> None:
    out_dir = tmp_path / "quickstart"
    stale = out_dir / "actual" / "stale.nii.gz"
    stale.parent.mkdir(parents=True)
    stale.write_text("stale", encoding="utf-8")

    run_synthetic_quickstart(out_dir, n_subjects=1, force=True)

    assert not stale.exists()
    assert (out_dir / "actual" / "sub-toy001.nii.gz").exists()
