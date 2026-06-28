from pathlib import Path

import nibabel as nib
import numpy as np

from hemispec.similarity import compute_specificity


def _save(path: Path, arr: np.ndarray) -> None:
    nib.save(nib.Nifti1Image(arr.astype(np.float32), np.eye(4)), str(path))


def test_specificity_full_volume_smoke(tmp_path):
    subjects = ["sub-MSC01", "sub-MSC02", "sub-MSC03"]
    scan_a = []
    scan_b = []
    for i, subject in enumerate(subjects):
        base = np.zeros((4, 4, 4), dtype=np.float32)
        base.flat[i * 5 : i * 5 + 5] = 1.0
        a = base.copy()
        b = base + 0.01
        pa = tmp_path / f"{subject}_run-01_ANS.nii.gz"
        pb = tmp_path / f"{subject}_run-02_ANS.nii.gz"
        _save(pa, a)
        _save(pb, b)
        scan_a.append(pa)
        scan_b.append(pb)

    result = compute_specificity(
        scan_a,
        scan_b,
        subjects=subjects,
        kind="ANS",
        hemi="ALL",
        mask_type="rate",
        thr=0,
        rate_thr=0.1,
        symmetrize=False,
    )
    assert result.matrix.shape == (3, 3)
    assert result.match_rate == 100.0
    assert result.specificity_index > 0

