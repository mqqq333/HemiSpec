from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd

from .io import list_from_glob, strip_nii_ext


@dataclass(frozen=True)
class RoiSummaryConfig:
    maps_glob: str
    atlas_path: Path
    out_csv: Path
    label_table: Path | None = None
    file_regex: str = r"(?P<subject>.+?)_(?P<kind>ANS|RNS)\.nii(?:\.gz)?$"
    stat: str = "mean"
    background_label: int = 0
    ignore_zero: bool = True


def summarize_maps_by_atlas(config: RoiSummaryConfig) -> pd.DataFrame:
    atlas_img = nib.load(str(config.atlas_path))
    atlas = np.squeeze(atlas_img.get_fdata()).astype(np.int32)
    labels = [int(x) for x in np.unique(atlas) if int(x) != int(config.background_label)]
    label_names = _load_label_names(config.label_table)
    rows: list[dict[str, object]] = []

    for map_path in list_from_glob(config.maps_glob):
        map_img = nib.load(str(map_path))
        data = np.squeeze(map_img.get_fdata(dtype=np.float32))
        _assert_compatible(atlas_img, atlas, map_img, data, map_path)
        meta = _parse_map_name(map_path, config.file_regex)
        values_by_label = _summarize_values_by_label(
            data,
            atlas,
            labels,
            stat=config.stat,
            ignore_zero=config.ignore_zero,
            background_label=config.background_label,
        )

        for label, (value, n_voxels) in zip(labels, values_by_label):
            rows.append(
                {
                    **meta,
                    "atlas": config.atlas_path.stem,
                    "roi_label": label,
                    "roi_name": label_names.get(label, ""),
                    "stat": config.stat,
                    "value": value,
                    "n_voxels": n_voxels,
                    "map_path": str(map_path),
                }
            )

    df = pd.DataFrame(rows)
    config.out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(config.out_csv, index=False)
    return df


def _summarize_values_by_label(
    data: np.ndarray,
    atlas: np.ndarray,
    labels: list[int],
    *,
    stat: str,
    ignore_zero: bool,
    background_label: int,
) -> list[tuple[float, int]]:
    if stat == "mean":
        return _mean_values_by_label(data, atlas, labels, ignore_zero=ignore_zero, background_label=background_label)
    if stat == "median":
        return _median_values_by_label(data, atlas, labels, ignore_zero=ignore_zero)
    raise ValueError("ROI stat must be one of: mean, median")


def _mean_values_by_label(
    data: np.ndarray,
    atlas: np.ndarray,
    labels: list[int],
    *,
    ignore_zero: bool,
    background_label: int,
) -> list[tuple[float, int]]:
    """Compute per-label means with one vectorized pass over the map.

    The previous implementation sliced the full 3D image once per ROI label
    (`data[atlas == label]`).  For whole-cortex Glasser exports this repeated
    scan dominates runtime.  `np.bincount` aggregates all labels in one pass
    while preserving the public CSV schema and ROI ordering.
    """

    if not labels:
        return []
    if min(labels) < 0:
        return _mean_values_by_label_slow(data, atlas, labels, ignore_zero=ignore_zero)

    flat_labels = atlas.ravel()
    flat_values = data.ravel()
    valid = (flat_labels != int(background_label)) & np.isfinite(flat_values)
    if ignore_zero:
        valid &= flat_values != 0

    label_values = flat_labels[valid].astype(np.int64, copy=False)
    value_values = flat_values[valid].astype(np.float64, copy=False)
    minlength = max(labels) + 1
    sums = np.bincount(label_values, weights=value_values, minlength=minlength)
    counts = np.bincount(label_values, minlength=minlength)

    out: list[tuple[float, int]] = []
    for label in labels:
        count = int(counts[label]) if label < len(counts) else 0
        value = float(sums[label] / count) if count else float("nan")
        out.append((value, count))
    return out


def _mean_values_by_label_slow(
    data: np.ndarray,
    atlas: np.ndarray,
    labels: list[int],
    *,
    ignore_zero: bool,
) -> list[tuple[float, int]]:
    out: list[tuple[float, int]] = []
    for label in labels:
        values = data[atlas == label]
        values = values[np.isfinite(values)]
        if ignore_zero:
            values = values[values != 0]
        out.append((float(np.mean(values)) if values.size else float("nan"), int(values.size)))
    return out


def _median_values_by_label(
    data: np.ndarray,
    atlas: np.ndarray,
    labels: list[int],
    *,
    ignore_zero: bool,
) -> list[tuple[float, int]]:
    out: list[tuple[float, int]] = []
    for label in labels:
        values = data[atlas == label]
        values = values[np.isfinite(values)]
        if ignore_zero:
            values = values[values != 0]
        out.append((float(np.median(values)) if values.size else float("nan"), int(values.size)))
    return out


def _parse_map_name(path: Path, pattern: str) -> dict[str, object]:
    match = re.search(pattern, path.name)
    if match:
        groups = match.groupdict()
        if groups:
            return groups
        values = match.groups()
        if len(values) >= 2:
            return {"subject": values[0], "kind": values[1]}
    stem = strip_nii_ext(path.name)
    kind = "ANS" if "_ANS" in stem.upper() else "RNS" if "_RNS" in stem.upper() else ""
    return {"subject": stem, "kind": kind}


def _assert_compatible(atlas_img, atlas: np.ndarray, map_img, data: np.ndarray, map_path: Path) -> None:
    if data.shape != atlas.shape:
        raise RuntimeError(f"Shape mismatch for {map_path}: {data.shape} vs atlas {atlas.shape}")
    if not np.allclose(map_img.affine, atlas_img.affine, atol=1e-4):
        raise RuntimeError(f"Affine mismatch for {map_path} vs atlas {atlas_img.get_filename()}")


def _load_label_names(path: Path | None) -> dict[int, str]:
    if path is None or not path.exists():
        return {}
    suffix = path.suffix.lower()
    try:
        if suffix in {".csv", ".tsv"}:
            sep = "\t" if suffix == ".tsv" else ","
            table = pd.read_csv(path, sep=sep)
        elif suffix in {".xlsx", ".xls"}:
            table = pd.read_excel(path)
        else:
            return {}
    except ImportError:
        return {}

    paired = _label_names_from_paired_hemisphere_table(table)
    if paired:
        return paired

    label_col = _first_existing_column(table, ("label", "index", "id", "roi_label", "Label", "Index", "ID"))
    name_col = _first_existing_column(table, ("name", "label_name", "roi_name", "region", "Name", "Region"))
    if label_col is None or name_col is None:
        return {}
    result: dict[int, str] = {}
    for _, row in table.iterrows():
        try:
            result[int(row[label_col])] = str(row[name_col])
        except (TypeError, ValueError):
            continue
    return result


def _label_names_from_paired_hemisphere_table(table: pd.DataFrame) -> dict[int, str]:
    pairs = (
        ("left_label_index", "left_label_name"),
        ("right_label_index", "right_label_name"),
    )
    if not all(label in table.columns and name in table.columns for label, name in pairs):
        return {}
    result: dict[int, str] = {}
    for label_col, name_col in pairs:
        for _, row in table.iterrows():
            try:
                result[int(row[label_col])] = str(row[name_col])
            except (TypeError, ValueError):
                continue
    return result


def _first_existing_column(table: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    for col in candidates:
        if col in table.columns:
            return col
    return None
