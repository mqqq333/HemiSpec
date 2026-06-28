from pathlib import Path

import nibabel as nib
import numpy as np

from hemispec.compute import compute_ans_rns_arrays, run_compute


def test_compute_ans_rns_arrays_formula():
    gm = np.array([0.2, 0.1, 0.4], dtype=np.float32)
    recon = np.array([0.1, 0.0, 0.2], dtype=np.float32)
    ans, rns, valid = compute_ans_rns_arrays(gm, recon, gm_thresh=0.15, eps=1e-6)
    assert valid.tolist() == [True, False, True]
    np.testing.assert_allclose(ans, [0.1, 0.0, 0.2], atol=1e-6)
    np.testing.assert_allclose(rns[[0, 2]], [0.1 / 0.300001, 0.2 / 0.600001], atol=1e-6)


def _save(path: Path, arr: np.ndarray) -> None:
    nib.save(nib.Nifti1Image(arr.astype(np.float32), np.eye(4)), str(path))


def test_run_compute_smoke(tmp_path):
    gm_dir = tmp_path / "gm"
    pred_dir = tmp_path / "pred"
    out_dir = tmp_path / "out"
    gm_dir.mkdir()
    pred_dir.mkdir()

    gm = np.full((4, 4, 4), 0.2, dtype=np.float32)
    pred = np.full((4, 4, 4), 0.1, dtype=np.float32)
    _save(gm_dir / "sub-01_run-01.nii.gz", gm)
    _save(pred_dir / "sub-01_run-01_PRED_LR_full.nii.gz", pred)

    res = run_compute(
        str(gm_dir / "*.nii.gz"),
        str(pred_dir / "*.nii.gz"),
        out_dir,
        save_subject_maps=True,
        verbose_every=0,
    )

    assert res["n_pairs"] == 1
    assert (out_dir / "ANS_group_masked_mean.nii.gz").exists()
    assert (out_dir / "RNS_group_masked_mean.nii.gz").exists()
    ans = nib.load(str(out_dir / "ANS_group_masked_mean.nii.gz")).get_fdata()
    assert np.isclose(ans.mean(), 0.1)

