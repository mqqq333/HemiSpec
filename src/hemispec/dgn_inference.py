from __future__ import annotations

from concurrent.futures import CancelledError
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np

from .io import list_from_glob, load_nifti, save_like, strip_nii_ext


LEFT_SLICE = (slice(60, 115), slice(15, 134), slice(15, 102))
RIGHT_SLICE = (slice(5, 60), slice(15, 134), slice(15, 102))
MIN_INPUT_SHAPE = (115, 134, 102)
INFERENCE_MASK_THRESHOLD = 0.05


@dataclass(frozen=True)
class DGNInferenceOutput:
    input_path: Path
    output_path: Path
    direction: str


def source_slice(direction: str) -> tuple[slice, slice, slice]:
    direction = direction.upper()
    if direction == "L_TO_R":
        return LEFT_SLICE
    if direction == "R_TO_L":
        return RIGHT_SLICE
    raise ValueError("direction must be L_to_R or R_to_L")


def target_slice(direction: str) -> tuple[slice, slice, slice]:
    direction = direction.upper()
    if direction == "L_TO_R":
        return RIGHT_SLICE
    if direction == "R_TO_L":
        return LEFT_SLICE
    raise ValueError("direction must be L_to_R or R_to_L")


def apply_inference_input_mask(volume: np.ndarray, threshold: float = INFERENCE_MASK_THRESHOLD) -> np.ndarray:
    return np.where(volume > float(threshold), volume, 0).astype(np.float32, copy=False)


def crop_source(volume: np.ndarray, direction: str) -> np.ndarray:
    _check_volume_shape(volume)
    z, y, x = source_slice(direction)
    return volume[z, y, x].astype(np.float32, copy=False)


def paste_prediction(
    volume: np.ndarray,
    prediction: np.ndarray,
    direction: str,
    mask_target: bool = True,
) -> np.ndarray:
    _check_volume_shape(volume)
    out = volume.astype(np.float32, copy=True)
    z, y, x = target_slice(direction)
    pred = np.squeeze(prediction).astype(np.float32, copy=False)
    expected_shape = out[z, y, x].shape
    if pred.shape != expected_shape:
        raise RuntimeError(f"DGN prediction shape mismatch: {pred.shape} vs target ROI {expected_shape}")
    if mask_target:
        mask = out[z, y, x] > 0
        out[z, y, x] = out[z, y, x] * (~mask) + pred * mask
    else:
        out[z, y, x] = pred
    return out


def run_dgn_on_volume(
    volume: np.ndarray,
    model,
    direction: str,
    device: str,
    clip_recon: tuple[float, float] | None = None,
) -> np.ndarray:
    try:
        import torch
    except ImportError as exc:
        raise ImportError("DGN inference requires PyTorch.") from exc

    masked = apply_inference_input_mask(np.squeeze(volume))
    src = crop_source(masked, direction)
    tensor = torch.from_numpy(src[np.newaxis, np.newaxis].astype(np.float32)).to(device)
    with torch.inference_mode():
        pred = model(tensor).detach().cpu().numpy()[0, 0]
    if clip_recon is not None:
        pred = np.clip(pred, clip_recon[0], clip_recon[1])
    return paste_prediction(masked, pred, direction)


def run_dgn_inference_files(
    input_glob: str,
    out_dir: str | Path,
    model,
    direction: str,
    device: str,
    output_suffix: str = "_PRED_LR_full.nii.gz",
    clip_recon: tuple[float, float] | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> list[DGNInferenceOutput]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    inputs = list_from_glob(input_glob)
    if not inputs:
        raise RuntimeError(f"No input GM maps matched: {input_glob}")

    outputs: list[DGNInferenceOutput] = []
    for idx, path in enumerate(inputs, start=1):
        _raise_if_cancelled(should_cancel)
        print(f"[infer] {direction} {idx}/{len(inputs)} start {path.name}")
        nifti = load_nifti(path)
        recon = run_dgn_on_volume(
            nifti.data,
            model=model,
            direction=direction,
            device=device,
            clip_recon=clip_recon,
        )
        output_path = out / f"{strip_nii_ext(path.name)}{output_suffix}"
        save_like(nifti.image, recon, output_path)
        print(f"[infer] {direction} {idx}/{len(inputs)} done {output_path.name}")
        outputs.append(DGNInferenceOutput(input_path=path, output_path=output_path, direction=direction))
    return outputs


def _raise_if_cancelled(should_cancel: Callable[[], bool] | None) -> None:
    if should_cancel is not None and should_cancel():
        raise CancelledError("Workflow cancelled by user.")


def _check_volume_shape(volume: np.ndarray) -> None:
    if volume.ndim != 3:
        raise ValueError(f"Expected 3D GM volume, got shape {volume.shape}")
    if any(got < need for got, need in zip(volume.shape, MIN_INPUT_SHAPE)):
        raise ValueError(f"GM volume shape too small {volume.shape}; expected at least {MIN_INPUT_SHAPE}")
