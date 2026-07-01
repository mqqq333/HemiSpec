from __future__ import annotations

import shutil
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd

from .api import MetricComputeConfig, compute_metrics


def _save_nifti(path: Path, data: np.ndarray, affine: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = nib.Nifti1Image(data.astype(np.float32, copy=False), affine)
    image.set_data_dtype(np.float32)
    nib.save(image, str(path))


def make_synthetic_quickstart_inputs(out_dir: Path, n_subjects: int = 3) -> None:
    """Create a tiny public-safe ANS/RNS compute fixture.

    The generated NIfTI files are deterministic toy arrays. They are not
    anatomical data and should only be used to validate the public command and
    file contract from a PyPI-installed package.
    """

    actual_dir = out_dir / "actual"
    recon_dir = out_dir / "recon"
    atlas_dir = out_dir / "atlas"
    actual_dir.mkdir(parents=True, exist_ok=True)
    recon_dir.mkdir(parents=True, exist_ok=True)
    atlas_dir.mkdir(parents=True, exist_ok=True)

    shape = (16, 14, 12)
    affine = np.diag([1.5, 1.5, 1.5, 1.0])
    z, y, x = np.indices(shape, dtype=np.float32)
    center = np.array([(shape[0] - 1) / 2, (shape[1] - 1) / 2, (shape[2] - 1) / 2], dtype=np.float32)
    radius2 = ((z - center[0]) / 6.0) ** 2 + ((y - center[1]) / 5.0) ** 2 + ((x - center[2]) / 4.0) ** 2
    gm_template = 0.08 + 0.62 * np.exp(-radius2)

    for idx in range(1, n_subjects + 1):
        subject = f"sub-toy{idx:03d}"
        subject_bias = (idx - 2) * 0.015
        lateral_gradient = 0.025 * (x - center[2]) / max(center[2], 1)
        actual = np.clip(gm_template + subject_bias + lateral_gradient, 0, 1)

        target_region = (x >= center[2]) & (z > center[0] - 3) & (z < center[0] + 4)
        dorsal_region = y >= center[1]
        left_like_region = (x < center[2]) & (y < center[1]) & (gm_template >= 0.15)
        recon = actual.copy()
        recon[target_region] -= 0.035 + 0.005 * idx
        recon[dorsal_region] += 0.015
        recon[left_like_region] += 0.012
        recon = np.clip(recon, 0, 1)

        _save_nifti(actual_dir / f"{subject}.nii.gz", actual, affine)
        _save_nifti(recon_dir / f"{subject}_PRED_LR_full.nii.gz", recon, affine)

    atlas = np.zeros(shape, dtype=np.int16)
    atlas[(x < center[2]) & (gm_template >= 0.15)] = 1
    atlas[(x >= center[2]) & (gm_template >= 0.15)] = 2
    atlas[(y >= center[1]) & (gm_template >= 0.15)] = 3
    atlas_image = nib.Nifti1Image(atlas, affine)
    atlas_image.set_data_dtype(np.int16)
    nib.save(atlas_image, str(atlas_dir / "toy_atlas.nii.gz"))

    pd.DataFrame(
        [
            {"label": 1, "name": "Toy left-like ROI"},
            {"label": 2, "name": "Toy right-like ROI"},
            {"label": 3, "name": "Toy dorsal ROI"},
        ]
    ).to_csv(atlas_dir / "toy_labels.csv", index=False)

    (out_dir / "README.generated.txt").write_text(
        "Synthetic HemiSpec quickstart fixture. Not real neuroimaging data.\n"
        "Generated actual maps, mock DGN reconstructions, and toy atlas.\n",
        encoding="utf-8",
    )


def run_synthetic_quickstart(out_dir: Path, n_subjects: int = 3, force: bool = False) -> dict[str, Path | int]:
    """Generate toy inputs and run the public-safe compute workflow."""

    out_dir = Path(out_dir)
    if out_dir.exists() and any(out_dir.iterdir()) and not force:
        raise FileExistsError(
            f"Output directory is not empty: {out_dir}. "
            "Choose a new --out-dir or pass --force to overwrite generated files."
        )
    if out_dir.exists() and force:
        shutil.rmtree(out_dir)

    make_synthetic_quickstart_inputs(out_dir, n_subjects=n_subjects)
    compute_out = out_dir / "outputs" / "compute"
    roi_csv = compute_out / "toy_roi_summary.csv"
    result = compute_metrics(
        MetricComputeConfig(
            actual_glob=str(out_dir / "actual" / "*.nii.gz"),
            reconstructed_glob=str(out_dir / "recon" / "*_PRED_LR_full.nii.gz"),
            out_dir=compute_out,
            save_subject_maps=True,
            roi_atlas=out_dir / "atlas" / "toy_atlas.nii.gz",
            roi_label_table=out_dir / "atlas" / "toy_labels.csv",
            roi_out_csv=roi_csv,
            verbose_every=1,
        )
    )
    return {
        "out_dir": out_dir,
        "compute_out": result.out_dir,
        "roi_csv": result.roi_csv or roi_csv,
        "n_pairs": result.n_pairs,
    }
