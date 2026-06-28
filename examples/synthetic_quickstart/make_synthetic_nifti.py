from __future__ import annotations

import argparse
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd


def _save_nifti(path: Path, data: np.ndarray, affine: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = nib.Nifti1Image(data.astype(np.float32, copy=False), affine)
    img.set_data_dtype(np.float32)
    nib.save(img, str(path))


def make_example(out_dir: Path, n_subjects: int = 3) -> None:
    actual_dir = out_dir / "actual"
    recon_dir = out_dir / "recon"
    atlas_dir = out_dir / "atlas"
    actual_dir.mkdir(parents=True, exist_ok=True)
    recon_dir.mkdir(parents=True, exist_ok=True)
    atlas_dir.mkdir(parents=True, exist_ok=True)

    shape = (16, 14, 12)  # small z, y, x fixture; not anatomical data
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

        # A deterministic mock reconstruction: similar to actual GM, but with a
        # small lateralized residual so ANS/RNS outputs are non-zero.
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
    atlas_img = nib.Nifti1Image(atlas, affine)
    atlas_img.set_data_dtype(np.int16)
    nib.save(atlas_img, str(atlas_dir / "toy_atlas.nii.gz"))

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


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic, public-safe HemiSpec quickstart NIfTI fixtures.")
    parser.add_argument("--out-dir", default=None, help="Directory for generated synthetic inputs and outputs. Defaults to ./workdir next to this script.")
    parser.add_argument("--n-subjects", type=int, default=3, help="Number of toy subjects to generate.")
    args = parser.parse_args()
    out_dir = Path(args.out_dir) if args.out_dir else Path(__file__).resolve().parent / "workdir"
    make_example(out_dir, n_subjects=args.n_subjects)
    print(f"[done] synthetic quickstart data written to {out_dir.resolve()}")


if __name__ == "__main__":
    main()
