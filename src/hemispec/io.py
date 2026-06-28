from __future__ import annotations

import glob
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import nibabel as nib
import numpy as np


NII_SUFFIXES = (".nii.gz", ".nii")


@dataclass(frozen=True)
class NiftiData:
    path: Path
    image: nib.Nifti1Image
    data: np.ndarray


@dataclass(frozen=True)
class MapPair:
    key: str
    actual: Path
    predicted: Path


def strip_nii_ext(name: str) -> str:
    lower = name.lower()
    if lower.endswith(".nii.gz"):
        return name[:-7]
    if lower.endswith(".nii"):
        return name[:-4]
    return name


def load_nifti(path: str | os.PathLike[str]) -> NiftiData:
    p = Path(path)
    img = nib.load(str(p))
    data = np.squeeze(img.get_fdata(dtype=np.float32))
    return NiftiData(path=p, image=img, data=data)


def save_like(
    reference: nib.Nifti1Image,
    data: np.ndarray,
    out_path: str | os.PathLike[str],
    dtype: np.dtype | type = np.float32,
) -> None:
    out = nib.Nifti1Image(data.astype(dtype, copy=False), reference.affine, reference.header)
    out.set_data_dtype(dtype)
    nib.save(out, str(out_path))


def list_from_glob(pattern: str) -> list[Path]:
    files = [Path(p) for p in sorted(glob.glob(pattern))]
    return [p for p in files if p.name.lower().endswith(NII_SUFFIXES)]


def list_nifti_files(path: str | os.PathLike[str]) -> list[Path]:
    root = Path(path)
    return [
        p
        for p in sorted(root.iterdir())
        if p.is_file() and p.name.lower().endswith(NII_SUFFIXES)
    ]


def _key_from_path(path: Path, suffix_to_strip: str = "") -> str:
    key = strip_nii_ext(path.name)
    if suffix_to_strip and key.endswith(suffix_to_strip):
        key = key[: -len(suffix_to_strip)]
    return key


def build_pairs(
    actual_files: Iterable[Path],
    predicted_files: Iterable[Path],
    pred_suffix_to_strip: str = "_PRED_LR_full",
    actual_suffix_to_strip: str = "",
) -> tuple[list[MapPair], list[str], list[str]]:
    actual_map = {_key_from_path(p, actual_suffix_to_strip): p for p in actual_files}
    pred_map = {_key_from_path(p, pred_suffix_to_strip): p for p in predicted_files}
    keys = sorted(set(actual_map).intersection(pred_map))
    missing_actual = sorted(set(pred_map) - set(actual_map))
    missing_pred = sorted(set(actual_map) - set(pred_map))
    pairs = [MapPair(k, actual_map[k], pred_map[k]) for k in keys]
    return pairs, missing_actual, missing_pred


def assert_compatible(reference: NiftiData, other: NiftiData, label: str) -> None:
    if other.data.shape != reference.data.shape:
        raise RuntimeError(
            f"Shape mismatch for {label}: {other.path} {other.data.shape} vs "
            f"{reference.path} {reference.data.shape}"
        )
    if not np.allclose(other.image.affine, reference.image.affine, atol=1e-4):
        raise RuntimeError(f"Affine mismatch for {label}: {other.path} vs {reference.path}")

