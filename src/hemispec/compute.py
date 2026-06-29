from __future__ import annotations

from concurrent.futures import CancelledError
from pathlib import Path
from typing import Callable

import numpy as np

from .io import assert_compatible, build_pairs, list_from_glob, load_nifti, save_like


def compute_ans_rns_arrays(
    gm: np.ndarray,
    recon: np.ndarray,
    gm_thresh: float = 0.15,
    eps: float = 1e-6,
    clip_recon: tuple[float, float] | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if clip_recon is not None:
        lo, hi = clip_recon
        recon = np.clip(recon, lo, hi)

    valid = np.isfinite(gm) & np.isfinite(recon) & (gm >= float(gm_thresh))
    ans = np.zeros(gm.shape, dtype=np.float32)
    rns = np.zeros(gm.shape, dtype=np.float32)

    if np.any(valid):
        diff = np.abs(gm - recon).astype(np.float32, copy=False)
        denom = (np.abs(gm) + np.abs(recon) + float(eps)).astype(np.float32, copy=False)
        ans[valid] = diff[valid]
        rns[valid] = diff[valid] / denom[valid]

    return ans, rns, valid


def run_compute(
    actual_glob: str,
    predicted_glob: str,
    out_dir: str | Path,
    gm_thresh: float = 0.15,
    eps: float = 1e-6,
    pred_suffix_to_strip: str = "_PRED_LR_full",
    actual_suffix_to_strip: str = "",
    clip_recon: tuple[float, float] | None = None,
    save_subject_maps: bool = False,
    save_group_maps: bool = True,
    write_nan_outside: bool = False,
    verbose_every: int = 50,
    should_cancel: Callable[[], bool] | None = None,
) -> dict[str, object]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    subject_dir = out / "subject_maps"
    if save_subject_maps:
        subject_dir.mkdir(parents=True, exist_ok=True)

    actual_files = list_from_glob(actual_glob)
    predicted_files = list_from_glob(predicted_glob)
    if not actual_files:
        raise RuntimeError(f"No actual GM maps matched: {actual_glob}")
    if not predicted_files:
        raise RuntimeError(f"No predicted/reconstructed maps matched: {predicted_glob}")

    pairs, missing_actual, missing_pred = build_pairs(
        actual_files,
        predicted_files,
        pred_suffix_to_strip=pred_suffix_to_strip,
        actual_suffix_to_strip=actual_suffix_to_strip,
    )
    if not pairs:
        raise RuntimeError("No paired maps found. Check globs and suffix stripping options.")

    ref = load_nifti(pairs[0].actual)
    shape = ref.data.shape
    ans_sum = np.zeros(shape, dtype=np.float64)
    rns_sum = np.zeros(shape, dtype=np.float64)
    valid_n = np.zeros(shape, dtype=np.int32)

    for idx, pair in enumerate(pairs, start=1):
        _raise_if_cancelled(should_cancel)
        actual = load_nifti(pair.actual)
        predicted = load_nifti(pair.predicted)
        assert_compatible(ref, actual, "actual GM")
        assert_compatible(ref, predicted, "predicted/reconstructed GM")

        ans, rns, valid = compute_ans_rns_arrays(
            actual.data,
            predicted.data,
            gm_thresh=gm_thresh,
            eps=eps,
            clip_recon=clip_recon,
        )
        if np.any(valid):
            ans_sum[valid] += ans[valid].astype(np.float64)
            rns_sum[valid] += rns[valid].astype(np.float64)
            valid_n[valid] += 1

        if save_subject_maps:
            if write_nan_outside:
                ans_out = np.full(shape, np.nan, dtype=np.float32)
                rns_out = np.full(shape, np.nan, dtype=np.float32)
                ans_out[valid] = ans[valid]
                rns_out[valid] = rns[valid]
            else:
                ans_out = ans
                rns_out = rns
            save_like(ref.image, ans_out, subject_dir / f"{pair.key}_ANS.nii.gz")
            save_like(ref.image, rns_out, subject_dir / f"{pair.key}_RNS.nii.gz")

        if verbose_every > 0 and (idx % verbose_every == 0 or idx == len(pairs)):
            valid_frac = float(valid.mean())
            print(f"[compute] {idx}/{len(pairs)} done {pair.key} valid_voxel_fraction={valid_frac:.4f}")

    _raise_if_cancelled(should_cancel)
    mask_any = valid_n > 0
    ans_mean = np.zeros(shape, dtype=np.float32)
    rns_mean = np.zeros(shape, dtype=np.float32)
    ans_mean[mask_any] = (ans_sum[mask_any] / valid_n[mask_any]).astype(np.float32)
    rns_mean[mask_any] = (rns_sum[mask_any] / valid_n[mask_any]).astype(np.float32)
    coverage = valid_n.astype(np.float32) / float(len(pairs))

    if save_group_maps:
        save_like(ref.image, ans_mean, out / "ANS_group_masked_mean.nii.gz")
        save_like(ref.image, rns_mean, out / "RNS_group_masked_mean.nii.gz")
        save_like(ref.image, valid_n, out / "validN.nii.gz", dtype=np.int32)
        save_like(ref.image, coverage, out / "coverage.nii.gz")

    return {
        "n_actual": len(actual_files),
        "n_predicted": len(predicted_files),
        "n_pairs": len(pairs),
        "missing_actual": missing_actual,
        "missing_predicted": missing_pred,
        "out_dir": str(out),
        "subject_maps_dir": str(subject_dir) if save_subject_maps else None,
        "group_maps_saved": save_group_maps,
    }


def _raise_if_cancelled(should_cancel: Callable[[], bool] | None) -> None:
    if should_cancel is not None and should_cancel():
        raise CancelledError("Workflow cancelled by user.")
