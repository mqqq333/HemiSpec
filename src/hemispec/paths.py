from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable


PACKAGE_DIR = Path(__file__).resolve().parent

DGN_MODEL_RELATIVE = Path("assets") / "models" / "dgn"
DGN_LEGACY_DIRS = ("outputs_bi_stable_L", "outputs_bi_stable_R")

CLASSIFIER_BUNDLE_NAME = "OUT_noICBM_train_ICBM_external_saved_models"
CLASSIFIER_PAIRED_RESIDUAL_BUNDLE_NAME = "OUT_noICBM_train_ICBM_external_saved_models_paired_residual"
CLASSIFIER_MODEL_RELATIVE = Path("assets") / "models" / "hemisphere_classifier" / CLASSIFIER_BUNDLE_NAME

GLASSER_ATLAS_RELATIVE = Path("assets") / "atlases" / "glasser" / "MNI_Glasser_HCP_v1.0_1p5mm.nii.gz"
GLASSER_LABEL_TABLE_RELATIVE = Path("assets") / "atlases" / "glasser" / "Glasser_label_index_mapping.xlsx"

EXAMPLE_INPUT_RELATIVE = Path("examples") / "input_sample"
TRT_DATA_RELATIVE = Path("data") / "TRT_data"
TRT_OUTPUTS_RELATIVE = Path("outputs") / "TRT_outputs"
CLASSIFIER_OUTPUTS_RELATIVE = Path("outputs") / "classifier_outputs"

PREPROCESS_ASSET_RELATIVE = Path("assets") / "preprocess" / "process_single_subject_GM_v2_reorient.sh"

ASSET_ROOT_ENV = ("HEMISPEC_ASSET_ROOT",)
MODEL_CACHE_ENV = ("HEMISPEC_MODEL_CACHE",)
DGN_MODEL_ROOT_ENV = ("HEMISPEC_DGN_MODEL_ROOT", "HEMISPEC_MODEL_ROOT")
CLASSIFIER_MODEL_DIR_ENV = ("HEMISPEC_CLASSIFIER_MODEL_DIR",)
ATLAS_PATH_ENV = ("HEMISPEC_GLASSER_ATLAS",)
LABEL_TABLE_ENV = ("HEMISPEC_GLASSER_LABEL_TABLE",)


def find_project_root(start: str | Path | None = None) -> Path:
    """Return the nearest HemiSpec checkout/distribution root we can infer."""

    for root in _iter_root_candidates(start):
        if (root / "assets").exists():
            return root
        if (root / "pyproject.toml").exists() and (root / "src" / "hemispec").exists():
            return root
    return Path.cwd()


def project_path(relative: str | Path, start: str | Path | None = None) -> Path:
    return find_project_root(start) / Path(relative)


def candidate_dgn_model_roots(root: str | Path | None = None) -> list[Path]:
    """Ordered DGN model roots.

    A root may be the model directory itself, a project root containing
    assets/models/dgn, or a legacy project root containing outputs_bi_stable_L/R.
    """

    candidates: list[Path] = []
    if root is not None:
        base = Path(root)
        candidates.extend(
            [
                base,
                base / DGN_MODEL_RELATIVE,
                base / "models" / "dgn",
                base / "dgn",
            ]
        )
        return _dedupe_paths(candidates)

    candidates.extend(_env_paths(DGN_MODEL_ROOT_ENV))
    for asset_root in _env_paths(ASSET_ROOT_ENV):
        candidates.append(asset_root / "models" / "dgn")

    for project_root in _iter_root_candidates():
        candidates.append(project_root / DGN_MODEL_RELATIVE)
        candidates.append(project_root)
    candidates.append(default_user_asset_root() / "models" / "dgn")
    return _dedupe_paths(candidates)


def resolve_dgn_model_root(root: str | Path | None = None) -> Path:
    for candidate in candidate_dgn_model_roots(root):
        if has_dgn_model_layout(candidate):
            return candidate
    if root is None:
        return default_user_asset_root() / "models" / "dgn"
    candidates = candidate_dgn_model_roots(root)
    return candidates[0] if candidates else project_path(DGN_MODEL_RELATIVE)


def has_dgn_model_layout(path: str | Path) -> bool:
    root = Path(path)
    return any((root / name / "ckpts").exists() for name in DGN_LEGACY_DIRS)


def resolve_classifier_model_dir(model_dir: str | Path | None = None, mode: str = "single") -> Path:
    if model_dir is not None:
        return Path(model_dir)

    bundle_name = _classifier_bundle_name_for_mode(mode)
    candidates: list[Path] = []
    candidates.extend(_env_paths(CLASSIFIER_MODEL_DIR_ENV))
    for asset_root in _env_paths(ASSET_ROOT_ENV):
        candidates.append(asset_root / "models" / "hemisphere_classifier" / bundle_name)
    for project_root in _iter_root_candidates():
        candidates.append(project_root / "assets" / "models" / "hemisphere_classifier" / bundle_name)
        candidates.append(project_root / "classifier_models" / bundle_name)
    candidates.append(default_user_asset_root() / "models" / "hemisphere_classifier" / bundle_name)

    for candidate in _dedupe_paths(candidates):
        if candidate.exists():
            return candidate
    return default_user_asset_root() / "models" / "hemisphere_classifier" / bundle_name


def default_user_asset_root() -> Path:
    """Writable per-user asset cache used by PyPI/GUI installs.

    Source checkouts usually resolve ``assets/models`` directly. Installed
    wheels and compiled apps use this cache when the released model files need
    to be downloaded outside the Python package.
    """

    cache_override = _first_env_path(MODEL_CACHE_ENV)
    if cache_override is not None:
        return cache_override
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
        return base / "HemiSpec" / "assets"
    base = Path(os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache"))
    return base / "hemispec" / "assets"


def is_default_dgn_model_root(path: str | Path | None) -> bool:
    if path is None:
        return True
    target = Path(path).expanduser().resolve()
    return any(target == candidate.expanduser().resolve() for candidate in candidate_dgn_model_roots(None))


def is_default_classifier_model_dir(path: str | Path | None, mode: str = "single") -> bool:
    if path is None:
        return True
    bundle_name = _classifier_bundle_name_for_mode(mode)
    target = Path(path).expanduser().resolve()
    candidates: list[Path] = []
    for asset_root in _env_paths(ASSET_ROOT_ENV):
        candidates.append(asset_root / "models" / "hemisphere_classifier" / bundle_name)
    for project_root in _iter_root_candidates():
        candidates.append(project_root / "assets" / "models" / "hemisphere_classifier" / bundle_name)
        candidates.append(project_root / "classifier_models" / bundle_name)
    candidates.append(default_user_asset_root() / "models" / "hemisphere_classifier" / bundle_name)
    return any(target == candidate.expanduser().resolve() for candidate in _dedupe_paths(candidates))


def _classifier_bundle_name_for_mode(mode: str | None) -> str:
    """Map a classifier ``mode`` alias to its model bundle directory name.

    Canonical modes are ``single`` and ``paired_residual``; common aliases
    (e.g. ``single_hemi``, ``paired``, ``pair_residual``) are tolerated.
    """
    value = (mode or "single").strip().lower().replace("-", "_")
    if value in {"single", "single_hemi", "single_hemisphere", "hemi_zscore"}:
        return CLASSIFIER_BUNDLE_NAME
    if value in {"paired", "paired_residual", "pair_residual", "subject_lr_residual", "subject_lr_residual_zscore"}:
        return CLASSIFIER_PAIRED_RESIDUAL_BUNDLE_NAME
    raise ValueError(
        f"Unknown classifier mode: {mode!r}. Expected one of: single, paired_residual "
        "(aliases: single_hemi, single_hemisphere, hemi_zscore, paired, pair_residual, "
        "subject_lr_residual, subject_lr_residual_zscore)."
    )


def resolve_glasser_atlas_path(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path)
    return _resolve_file_from_candidates(
        env_names=ATLAS_PATH_ENV,
        relative=GLASSER_ATLAS_RELATIVE,
        legacy_relative=Path("atlas") / GLASSER_ATLAS_RELATIVE.name,
    )


def resolve_glasser_label_table(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path)
    return _resolve_file_from_candidates(
        env_names=LABEL_TABLE_ENV,
        relative=GLASSER_LABEL_TABLE_RELATIVE,
        legacy_relative=Path("atlas") / GLASSER_LABEL_TABLE_RELATIVE.name,
    )


def resolve_sample_input_dir(project_root: str | Path | None = None) -> Path | None:
    for root in _iter_root_candidates(project_root):
        for relative in (EXAMPLE_INPUT_RELATIVE, Path("input_sample")):
            candidate = root / relative
            if candidate.exists():
                return candidate
    return None


def resolve_preprocess_script(project_root: str | Path | None = None) -> Path:
    package_script = PACKAGE_DIR / "resources" / "preprocess" / "process_single_subject_GM_v2_reorient.sh"
    candidates: list[Path] = []
    for root in _iter_root_candidates(project_root):
        candidates.extend(
            [
                root / PREPROCESS_ASSET_RELATIVE,
                root / "preprocess" / PREPROCESS_ASSET_RELATIVE.name,
            ]
        )
    candidates.append(package_script)
    for candidate in _dedupe_paths(candidates):
        if candidate.exists():
            return candidate
    return package_script


def default_input_glob() -> str:
    return str(project_path(TRT_DATA_RELATIVE / "*_GM_masked.nii.gz"))


def default_trt_output_path(*parts: str) -> Path:
    return project_path(TRT_OUTPUTS_RELATIVE.joinpath(*parts))


def default_classifier_output_path(*parts: str) -> Path:
    return project_path(CLASSIFIER_OUTPUTS_RELATIVE.joinpath(*parts))


def _resolve_file_from_candidates(
    env_names: Iterable[str],
    relative: Path,
    legacy_relative: Path,
) -> Path:
    candidates: list[Path] = []
    candidates.extend(_env_paths(env_names))
    for asset_root in _env_paths(ASSET_ROOT_ENV):
        candidates.append(asset_root / relative.relative_to("assets"))
    for project_root in _iter_root_candidates():
        candidates.append(project_root / relative)
        candidates.append(project_root / legacy_relative)

    for candidate in _dedupe_paths(candidates):
        if candidate.exists():
            return candidate
    return project_path(relative)


def _iter_root_candidates(start: str | Path | None = None) -> list[Path]:
    seeds: list[Path] = []
    if start is not None:
        seeds.append(Path(start))
    seeds.extend(
        [
            Path.cwd(),
            Path(sys.argv[0]).resolve().parent if sys.argv and sys.argv[0] else Path.cwd(),
            Path(sys.executable).resolve().parent if sys.executable else Path.cwd(),
            PACKAGE_DIR.parent.parent,
        ]
    )
    if getattr(sys, "frozen", False):
        seeds.append(Path(sys.executable).resolve().parent)
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            seeds.append(Path(meipass))

    roots: list[Path] = []
    for seed in seeds:
        seed = seed if seed.is_dir() else seed.parent
        for item in (seed, *seed.parents):
            roots.append(item)
    return _dedupe_paths(roots)




def _first_env_path(names: Iterable[str]) -> Path | None:
    paths = _env_paths(names)
    return paths[0] if paths else None


def _env_paths(names: Iterable[str]) -> list[Path]:
    paths: list[Path] = []
    for name in names:
        value = os.environ.get(name)
        if value:
            paths.append(Path(value))
    return paths


def _dedupe_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[str] = set()
    out: list[Path] = []
    for path in paths:
        key = str(path.expanduser().resolve()).lower()
        if key not in seen:
            seen.add(key)
            out.append(path)
    return out
