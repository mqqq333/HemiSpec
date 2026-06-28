from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.stats import ttest_ind

from .io import list_nifti_files, load_nifti


DEFAULT_HEMI_SLICES = {
    "L": (slice(60, 115), slice(15, 134), slice(15, 102)),
    "R": (slice(5, 60), slice(15, 134), slice(15, 102)),
}


@dataclass(frozen=True)
class SpecificityResult:
    kind: str
    hemi: str
    subjects: list[str]
    matrix: np.ndarray
    within: np.ndarray
    between: np.ndarray
    match_rate: float
    specificity_index: float
    cohen_d: float
    t_value: float
    p_value: float
    n_voxels: int


def parse_slice_spec(spec: str) -> slice:
    parts = [p.strip() for p in spec.split(":")]
    if len(parts) not in (2, 3):
        raise ValueError(f"Invalid slice spec: {spec!r}. Use START:STOP or START:STOP:STEP.")
    vals = [int(p) if p else None for p in parts]
    return slice(*vals)


def parse_hemi_slices(text: str | None) -> dict[str, tuple[slice, slice, slice]]:
    if not text:
        return DEFAULT_HEMI_SLICES
    out: dict[str, tuple[slice, slice, slice]] = {}
    for item in text.split(";"):
        item = item.strip()
        if not item:
            continue
        name, value = item.split("=", 1)
        axes = [parse_slice_spec(x) for x in value.split(",")]
        if len(axes) != 3:
            raise ValueError("Each custom hemi slice must have z,y,x slices.")
        out[name.strip().upper()] = (axes[0], axes[1], axes[2])
    return out


def crop_volume(vol: np.ndarray, hemi: str, hemi_slices: dict[str, tuple[slice, slice, slice]]) -> np.ndarray:
    hemi = hemi.upper()
    if hemi in ("ALL", "FULL"):
        return vol
    if hemi not in hemi_slices:
        raise ValueError(f"Unknown hemisphere/ROI {hemi!r}. Available: {sorted(hemi_slices)}")
    z, y, x = hemi_slices[hemi]
    return vol[z, y, x]


def compile_name_regex(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern)


def parse_subject_session(path: Path, regex: re.Pattern[str]) -> tuple[str, str] | None:
    match = regex.search(path.name)
    if not match:
        return None
    groups = match.groupdict()
    if "subject" in groups and "session" in groups:
        return groups["subject"], groups["session"]
    if match.lastindex and match.lastindex >= 2:
        return match.group(1), match.group(2)
    raise ValueError(
        "File regex must define named groups (?P<subject>...) and (?P<session>...), "
        "or at least two positional groups."
    )


def collect_session_maps(
    maps_dir: str | os.PathLike[str],
    suffix: str,
    file_regex: str,
) -> dict[str, dict[str, Path]]:
    regex = compile_name_regex(file_regex)
    out: dict[str, dict[str, Path]] = {}
    for path in list_nifti_files(maps_dir):
        if suffix and not path.name.endswith(suffix):
            continue
        parsed = parse_subject_session(path, regex)
        if parsed is None:
            continue
        subject, session = parsed
        out.setdefault(subject, {})[session] = path
    return out


def load_stack(
    paths: list[Path],
    hemi: str,
    hemi_slices: dict[str, tuple[slice, slice, slice]],
) -> np.ndarray:
    rows = []
    for path in paths:
        vol = load_nifti(path).data
        rows.append(crop_volume(vol, hemi, hemi_slices).reshape(-1))
    return np.vstack(rows).astype(np.float32)


def build_mask_rate(A: np.ndarray, B: np.ndarray, thr: float, rate_thr: float) -> np.ndarray:
    X = np.concatenate([A, B], axis=0)
    finite = np.isfinite(X)
    present = finite & (np.abs(X) > float(thr))
    return present.mean(axis=0) >= float(rate_thr)


def build_mask_max(A: np.ndarray, B: np.ndarray, thr: float, mode: str) -> np.ndarray:
    finite_a = np.isfinite(A)
    finite_b = np.isfinite(B)
    m_a = np.nanmax(np.where(finite_a, np.abs(A), np.nan), axis=0) > float(thr)
    m_b = np.nanmax(np.where(finite_b, np.abs(B), np.nan), axis=0) > float(thr)
    if mode == "intersect":
        return m_a & m_b
    return m_a | m_b


def pearson_matrix(A: np.ndarray, B: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    A = np.nan_to_num(A.astype(np.float64, copy=False), nan=0.0, posinf=0.0, neginf=0.0)
    B = np.nan_to_num(B.astype(np.float64, copy=False), nan=0.0, posinf=0.0, neginf=0.0)
    A = A - A.mean(axis=1, keepdims=True)
    B = B - B.mean(axis=1, keepdims=True)
    A /= np.sqrt((A * A).sum(axis=1, keepdims=True)) + eps
    B /= np.sqrt((B * B).sum(axis=1, keepdims=True)) + eps
    return (A @ B.T).astype(np.float32)


def spearman_matrix(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    Ar = np.argsort(np.argsort(np.nan_to_num(A), axis=1), axis=1).astype(np.float32) + 1.0
    Br = np.argsort(np.argsort(np.nan_to_num(B), axis=1), axis=1).astype(np.float32) + 1.0
    return pearson_matrix(Ar, Br)


def upper_offdiag(matrix: np.ndarray) -> np.ndarray:
    return matrix[np.triu_indices(matrix.shape[0], k=1)]


def cohen_d_independent(a: np.ndarray, b: np.ndarray) -> float:
    va = float(a.var(ddof=1)) if len(a) > 1 else 0.0
    vb = float(b.var(ddof=1)) if len(b) > 1 else 0.0
    pooled = np.sqrt((va + vb) / 2.0)
    if pooled == 0:
        return float("nan")
    return float((a.mean() - b.mean()) / pooled)


def compute_specificity(
    scan_a_paths: list[Path],
    scan_b_paths: list[Path],
    subjects: list[str],
    kind: str,
    hemi: str,
    metric: str = "pearson",
    mask_type: str = "rate",
    thr: float = 0.0,
    rate_thr: float = 0.3,
    mask_mode: str = "union",
    hemi_slices: dict[str, tuple[slice, slice, slice]] | None = None,
    symmetrize: bool = True,
) -> SpecificityResult:
    if len(scan_a_paths) != len(scan_b_paths):
        raise ValueError("scan_a_paths and scan_b_paths must have the same length.")
    if not scan_a_paths:
        raise ValueError("No paired maps were provided.")
    hemi_slices = hemi_slices or DEFAULT_HEMI_SLICES
    A0 = load_stack(scan_a_paths, hemi, hemi_slices)
    B0 = load_stack(scan_b_paths, hemi, hemi_slices)
    if A0.shape != B0.shape:
        raise RuntimeError(f"Stack shape mismatch: {A0.shape} vs {B0.shape}")

    if mask_type == "rate":
        mask = build_mask_rate(A0, B0, thr=thr, rate_thr=rate_thr)
    elif mask_type == "max":
        mask = build_mask_max(A0, B0, thr=thr, mode=mask_mode)
    else:
        raise ValueError("mask_type must be 'rate' or 'max'.")

    n_voxels = int(mask.sum())
    if n_voxels < 10:
        raise RuntimeError(
            f"Mask too small for {kind}.{hemi}: {n_voxels} voxels. "
            "Lower --thr/--rate-thr or check map values."
        )

    A = A0[:, mask]
    B = B0[:, mask]
    if metric == "pearson":
        S = pearson_matrix(A, B)
    elif metric == "spearman":
        S = spearman_matrix(A, B)
    else:
        raise ValueError("metric must be pearson or spearman.")

    matrix = 0.5 * (S + S.T) if symmetrize and S.shape[0] == S.shape[1] else S
    within = np.diag(matrix)
    between = upper_offdiag(matrix) if matrix.shape[0] == matrix.shape[1] else matrix[~np.eye(*matrix.shape, dtype=bool)]
    t_value, p_value = ttest_ind(within, between, equal_var=False)
    match_rate = float((S.argmax(axis=1) == np.arange(S.shape[0])).mean()) * 100.0
    specificity_index = float(within.mean() - between.mean())
    d_value = cohen_d_independent(within, between)

    return SpecificityResult(
        kind=kind,
        hemi=hemi,
        subjects=subjects,
        matrix=matrix,
        within=within,
        between=between,
        match_rate=match_rate,
        specificity_index=specificity_index,
        cohen_d=d_value,
        t_value=float(t_value),
        p_value=float(p_value),
        n_voxels=n_voxels,
    )


def paired_paths_for_sessions(
    maps_dir: str | os.PathLike[str],
    kind: str,
    session_a: str,
    session_b: str,
    suffix_template: str,
    file_regex: str,
) -> tuple[list[str], list[Path], list[Path]]:
    suffix = suffix_template.format(kind=kind)
    session_maps = collect_session_maps(maps_dir, suffix=suffix, file_regex=file_regex)
    subjects = sorted(
        subject
        for subject, sessions in session_maps.items()
        if session_a in sessions and session_b in sessions
    )
    scan_a = [session_maps[s][session_a] for s in subjects]
    scan_b = [session_maps[s][session_b] for s in subjects]
    return subjects, scan_a, scan_b

