from __future__ import annotations

import hashlib
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .paths import (
    CLASSIFIER_BUNDLE_NAME,
    CLASSIFIER_PAIRED_RESIDUAL_BUNDLE_NAME,
    default_user_asset_root,
)

DEFAULT_MODEL_ASSET_BASE_URL = "https://media.githubusercontent.com/media/mqqq333/HemiSpec/main"
BASE_URL_ENV = "HEMISPEC_MODEL_ASSET_BASE_URL"
AUTO_DOWNLOAD_ENV = "HEMISPEC_AUTO_DOWNLOAD_MODELS"
DISABLE_AUTO_DOWNLOAD_ENV = "HEMISPEC_DISABLE_MODEL_AUTO_DOWNLOAD"


@dataclass(frozen=True)
class ModelAsset:
    relative_path: str
    size: int
    sha256: str


DGN_MODEL_ASSETS: tuple[ModelAsset, ...] = (
    ModelAsset(
        "models/dgn/outputs_bi_stable_L/ckpts/best_netG_L.pth",
        153160817,
        "75d2146dec282c502a5dd32e43d1224205490747abf0f9e6faf49e645234c4fb",
    ),
    ModelAsset(
        "models/dgn/outputs_bi_stable_R/ckpts/best_netG_R.pth",
        153160817,
        "d677ca1725f23925190c2c5cda4c4482f4f83e1e57c7f7d90b71233250ee53b2",
    ),
)

CLASSIFIER_SINGLE_ASSETS: tuple[ModelAsset, ...] = (
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models/GLS_ANS/feature_names.csv", 2780, "eca32b423e0248246ed45f7e757b3bf3bae5e32a431ade5600b205957c034190"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models/GLS_ANS/GLS_ANS_final_pipeline.joblib", 7421, "9f8fe66759376d1796b411f24689b64bee5f70b934977dadc787ccea6dc1b30a"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models/GLS_ANS/GLS_ANS_noICBM_train_ICBM_test_model_bundle.joblib", 10918, "716858e9de1d6d705cf1fb1a7ad5156bdc2dc6cde33ca9ecac30d2aaf1baaf7d"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models/GLS_RNS/feature_names.csv", 2780, "e29c97cb5997d6ba1a10e8a96b188316f79ede5ca4f47ce7d6dc619510161c4a"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models/GLS_RNS/GLS_RNS_final_pipeline.joblib", 7421, "14690266bb898db87a83423abe9091b1155d5f9179026c7841774a0d0e6bcb21"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models/GLS_RNS/GLS_RNS_noICBM_train_ICBM_test_model_bundle.joblib", 10918, "93687c5c44ef5e2d58141d9e9f8117ff21987ee6955837332655ede5bba4daf4"),
)


CLASSIFIER_PAIRED_RESIDUAL_ASSETS: tuple[ModelAsset, ...] = (
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models_paired_residual/GLS_ANS/feature_names.csv", 2780, "eca32b423e0248246ed45f7e757b3bf3bae5e32a431ade5600b205957c034190"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models_paired_residual/GLS_ANS/GLS_ANS_final_pipeline.joblib", 7421, "076458050ca1fc92ded0ac15313a51df08ceeb7a69a6b961a3a57c4dd09faaf4"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models_paired_residual/GLS_ANS/GLS_ANS_noICBM_train_ICBM_test_model_bundle.joblib", 10942, "1312294d819e9d4465acde17855a3ce5bf1bd0c38312586fb4c4bae0ea7d3c08"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models_paired_residual/GLS_RNS/feature_names.csv", 2780, "e29c97cb5997d6ba1a10e8a96b188316f79ede5ca4f47ce7d6dc619510161c4a"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models_paired_residual/GLS_RNS/GLS_RNS_final_pipeline.joblib", 7421, "1071b4257209fdd553cd3b9a9dee93ad36f738a5d240f8f48f566d7f456bae13"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models_paired_residual/GLS_RNS/GLS_RNS_noICBM_train_ICBM_test_model_bundle.joblib", 10942, "cba745a7571ab5791af26e3b2f616c0df5ee485fe970e6c17e42fdcb0b6de688"),
)


def model_auto_download_enabled() -> bool:
    disabled = os.environ.get(DISABLE_AUTO_DOWNLOAD_ENV)
    if disabled is not None and not _is_falsey(disabled):
        return False
    explicit = os.environ.get(AUTO_DOWNLOAD_ENV)
    if explicit is not None:
        return not _is_falsey(explicit)
    return True


def ensure_default_dgn_models(destination_root: str | Path | None = None) -> Path:
    """Download missing released DGN checkpoints into the per-user asset cache."""

    asset_root = Path(destination_root) if destination_root is not None else default_user_asset_root()
    _ensure_assets(DGN_MODEL_ASSETS, asset_root, "DGN model")
    return asset_root / "models" / "dgn"


def ensure_default_classifier_models(mode: str = "single", destination_root: str | Path | None = None) -> Path:
    """Download missing released classifier bundles into the per-user asset cache."""

    asset_root = Path(destination_root) if destination_root is not None else default_user_asset_root()
    bundle_name, assets = _classifier_bundle_for_mode(mode)
    _ensure_assets(assets, asset_root, f"classifier bundle ({mode})")
    return asset_root / "models" / "hemisphere_classifier" / bundle_name


def ensure_default_model_assets(
    *,
    include_classifier: bool = False,
    classifier_mode: str = "single",
    destination_root: str | Path | None = None,
) -> Path:
    """Download the default runtime assets needed for model-enabled execution."""

    asset_root = Path(destination_root) if destination_root is not None else default_user_asset_root()
    ensure_default_dgn_models(asset_root)
    if include_classifier:
        ensure_default_classifier_models(classifier_mode, asset_root)
    return asset_root


def _ensure_assets(assets: Iterable[ModelAsset], asset_root: Path, label: str) -> None:
    if not model_auto_download_enabled():
        raise RuntimeError(
            f"Missing {label} files and automatic model download is disabled. "
            f"Unset {DISABLE_AUTO_DOWNLOAD_ENV} or set {AUTO_DOWNLOAD_ENV}=1."
        )
    asset_root.mkdir(parents=True, exist_ok=True)
    for asset in assets:
        target = asset_root / Path(asset.relative_path)
        if _existing_file_is_ready(target, asset):
            continue
        url = _asset_url(asset)
        print(f"[models] downloading {asset.relative_path} -> {target}")
        _download_asset(url, target, asset)


def _existing_file_is_ready(path: Path, asset: ModelAsset) -> bool:
    return path.exists() and path.stat().st_size == asset.size


def _download_asset(url: str, target: Path, asset: ModelAsset) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".download")
    digest = hashlib.sha256()
    written = 0
    try:
        with urllib.request.urlopen(url) as response, tmp.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
                digest.update(chunk)
                written += len(chunk)
                if asset.size >= 50_000_000 and written % (25 * 1024 * 1024) < len(chunk):
                    print(f"[models]   {written / (1024 * 1024):.0f} MB / {asset.size / (1024 * 1024):.0f} MB")
    except (OSError, urllib.error.URLError) as exc:
        if tmp.exists():
            tmp.unlink()
        raise RuntimeError(f"Could not download HemiSpec model asset from {url}: {exc}") from exc

    if written != asset.size:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(
            f"Downloaded {asset.relative_path} has unexpected size {written}; expected {asset.size}. "
            "Check network access and GitHub LFS availability."
        )
    actual_hash = digest.hexdigest()
    if actual_hash.lower() != asset.sha256.lower():
        tmp.unlink(missing_ok=True)
        raise RuntimeError(
            f"Downloaded {asset.relative_path} failed SHA256 verification: "
            f"{actual_hash} != {asset.sha256}."
        )
    tmp.replace(target)


def _asset_url(asset: ModelAsset) -> str:
    base = os.environ.get(BASE_URL_ENV, DEFAULT_MODEL_ASSET_BASE_URL).rstrip("/")
    return f"{base}/assets/{asset.relative_path}"


def _classifier_bundle_for_mode(mode: str) -> tuple[str, tuple[ModelAsset, ...]]:
    value = (mode or "single").strip().lower().replace("-", "_")
    if value in {"single", "single_hemi", "single_hemisphere", "hemi_zscore"}:
        return CLASSIFIER_BUNDLE_NAME, CLASSIFIER_SINGLE_ASSETS
    if value in {"paired", "paired_residual", "pair_residual", "subject_lr_residual", "subject_lr_residual_zscore"}:
        return CLASSIFIER_PAIRED_RESIDUAL_BUNDLE_NAME, CLASSIFIER_PAIRED_RESIDUAL_ASSETS
    if value == "all":
        return CLASSIFIER_BUNDLE_NAME, CLASSIFIER_SINGLE_ASSETS + CLASSIFIER_PAIRED_RESIDUAL_ASSETS
    raise ValueError("classifier mode must be single, paired_residual, or all")


def _is_falsey(value: str) -> bool:
    return value.strip().lower() in {"0", "false", "no", "off", "disabled"}


__all__ = [
    "AUTO_DOWNLOAD_ENV",
    "BASE_URL_ENV",
    "DISABLE_AUTO_DOWNLOAD_ENV",
    "DGN_MODEL_ASSETS",
    "CLASSIFIER_SINGLE_ASSETS",
    "CLASSIFIER_PAIRED_RESIDUAL_ASSETS",
    "ensure_default_classifier_models",
    "ensure_default_dgn_models",
    "ensure_default_model_assets",
    "model_auto_download_enabled",
]
