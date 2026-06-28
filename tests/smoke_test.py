from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import nibabel as nib
import numpy as np

from hemispec.compute import compute_ans_rns_arrays, run_compute


def save_nii(path: Path, arr: np.ndarray) -> None:
    nib.save(nib.Nifti1Image(arr.astype(np.float32), np.eye(4)), str(path))


def main() -> None:
    gm = np.array([0.2, 0.1, 0.4], dtype=np.float32)
    recon = np.array([0.1, 0.0, 0.2], dtype=np.float32)
    ans, rns, valid = compute_ans_rns_arrays(gm, recon, gm_thresh=0.15, eps=1e-6)
    assert valid.tolist() == [True, False, True]
    np.testing.assert_allclose(ans, [0.1, 0.0, 0.2], atol=1e-6)
    np.testing.assert_allclose(rns[[0, 2]], [0.1 / 0.300001, 0.2 / 0.600001], atol=1e-6)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        gm_dir = root / "gm"
        pred_dir = root / "pred"
        maps_dir = root / "maps"
        out_dir = root / "compute"
        spec_dir = root / "specificity"
        gm_dir.mkdir()
        pred_dir.mkdir()
        maps_dir.mkdir()

        gm_vol = np.full((4, 4, 4), 0.2, dtype=np.float32)
        pred_vol = np.full((4, 4, 4), 0.1, dtype=np.float32)
        save_nii(gm_dir / "sub-01_run-01.nii.gz", gm_vol)
        save_nii(pred_dir / "sub-01_run-01_PRED_LR_full.nii.gz", pred_vol)
        result = run_compute(
            str(gm_dir / "*.nii.gz"),
            str(pred_dir / "*.nii.gz"),
            out_dir,
            save_subject_maps=True,
            verbose_every=0,
        )
        assert result["n_pairs"] == 1
        assert (out_dir / "ANS_group_masked_mean.nii.gz").exists()
        assert (out_dir / "subject_maps" / "sub-01_run-01_ANS.nii.gz").exists()

        subjects = ["sub-MSC01", "sub-MSC02", "sub-MSC03"]
        for i, subject in enumerate(subjects):
            base = np.zeros((4, 4, 4), dtype=np.float32)
            base.flat[i * 5 : i * 5 + 5] = 1.0
            save_nii(maps_dir / f"{subject}_run-01_ANS.nii.gz", base)
            save_nii(maps_dir / f"{subject}_run-02_ANS.nii.gz", base + 0.01)
            save_nii(maps_dir / f"{subject}_run-01_RNS.nii.gz", base * 0.5)
            save_nii(maps_dir / f"{subject}_run-02_RNS.nii.gz", base * 0.5 + 0.01)

        subprocess.run(
            [
                sys.executable,
                "-m",
                "hemispec",
                "specificity",
                "--maps-dir",
                str(maps_dir),
                "--out-dir",
                str(spec_dir),
                "--hemis",
                "ALL",
                "--mask-type",
                "rate",
                "--rate-thr",
                "0.1",
                "--no-plots",
            ],
            check=True,
        )
        assert (spec_dir / "validation_summary.csv").exists()
        assert (spec_dir / "summary_ANS_ALL.txt").exists()

    print("smoke test passed")


if __name__ == "__main__":
    main()

