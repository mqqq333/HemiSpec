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
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models/all_model_summaries.csv", 1076, "235c1a4036afde31b88ce77e22ce6e6f91167fa5ca7ccf8edc7866ba8cf0524e"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models/all_model_summaries.json", 4703, "3f464ee219d295c002589dd9351398ced79bb6f4b16d9a1a4ff8c1b7493c44ed"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models/run_info.json", 584, "8462b9ea0f15540b2c9085d97e0207c9c475200ab402fe450941772405d06fee"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models/GLS_ANS/feature_names.csv", 2961, "0669035258d5129a24adc92e5220a1cc077a6b61b413d1fd9c287eef38e36bb3"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models/GLS_ANS/GLS_ANS_final_pipeline.joblib", 7421, "9f8fe66759376d1796b411f24689b64bee5f70b934977dadc787ccea6dc1b30a"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models/GLS_ANS/GLS_ANS_noICBM_train_ICBM_test_model_bundle.joblib", 11837, "958fc62ef9dd179deb1dca5f6a8d5c5140dcff065adff33aab92f9a54da0d609"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models/GLS_ANS/summary.json", 2189, "4469c0ea89bbb4e1a673d268a71da109b2a57523389085696209cc6cb5dc40a2"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models/GLS_ANS/summary.txt", 241, "79f5f0e696a75c1eb4af5e4a2e417ad490b8877dd3561ff68088f63eb3cf44db"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models/GLS_RNS/feature_names.csv", 2961, "7b5afb38543243490477e0d78b3009b636b2216f07b675706c1704db4fc0db2f"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models/GLS_RNS/GLS_RNS_final_pipeline.joblib", 7421, "14690266bb898db87a83423abe9091b1155d5f9179026c7841774a0d0e6bcb21"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models/GLS_RNS/GLS_RNS_noICBM_train_ICBM_test_model_bundle.joblib", 11837, "d0af3c404478ef6425c47be53115eb37c2e319675d28dc71b0ba56f94e6d2dff"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models/GLS_RNS/summary.json", 2133, "9141a3c2090a4770782674249f4eeb1e2200fac8b4f527678af31c2a84d5790a"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models/GLS_RNS/summary.txt", 210, "f8c4083d4f5dd3ab756fc1580298e8767a969b0a6b82811300d573c4572591c6"),
)

CLASSIFIER_PAIRED_RESIDUAL_ASSETS: tuple[ModelAsset, ...] = (
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models_paired_residual/all_model_summaries.csv", 1068, "f3ea287ddd24c9ecb4f0e09884b7026ee0f6c92be0064a9d359db20a866081e6"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models_paired_residual/all_model_summaries.json", 4622, "9714ad88213ab8dd31eb6b5b990018188375c1df0a984271530abf91359060bc"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models_paired_residual/run_info.json", 624, "e6b581d607ff7d452d8d9f26e29c73a1b07091d0f3bbd30208d3e0635500facd"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models_paired_residual/GLS_ANS/feature_names.csv", 2961, "0669035258d5129a24adc92e5220a1cc077a6b61b413d1fd9c287eef38e36bb3"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models_paired_residual/GLS_ANS/GLS_ANS_final_pipeline.joblib", 7421, "076458050ca1fc92ded0ac15313a51df08ceeb7a69a6b961a3a57c4dd09faaf4"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models_paired_residual/GLS_ANS/GLS_ANS_noICBM_train_ICBM_test_model_bundle.joblib", 11860, "f5b9b83dcc3d2e8547132b0cab4f25478eeca354c01cd05be855d9b0b920a553"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models_paired_residual/GLS_ANS/summary.json", 2129, "983c37b810241fb5192f56d948db9882eb645ef040bc7b441b9b58110f762e56"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models_paired_residual/GLS_ANS/summary.txt", 235, "df84edf850e46c2c2713d30f9b905c167cfbc4fa0ed8c8bee92df0b379891171"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models_paired_residual/GLS_RNS/feature_names.csv", 2961, "7b5afb38543243490477e0d78b3009b636b2216f07b675706c1704db4fc0db2f"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models_paired_residual/GLS_RNS/GLS_RNS_final_pipeline.joblib", 7421, "1071b4257209fdd553cd3b9a9dee93ad36f738a5d240f8f48f566d7f456bae13"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models_paired_residual/GLS_RNS/GLS_RNS_noICBM_train_ICBM_test_model_bundle.joblib", 11860, "ffd8009d738f410d9ba946bc42d9446f4267b49843c88e7575c31a65c88f5da6"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models_paired_residual/GLS_RNS/summary.json", 2112, "a376d8e7f8417ef52c1b48ca9c753b3e44c4cca99cff7dc8663325ae8b6da546"),
    ModelAsset("models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models_paired_residual/GLS_RNS/summary.txt", 235, "bbcb3cb2b51f4843045217c6def42091cd2f72888dbd2b6038c4eaac6f4db9a1"),
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
