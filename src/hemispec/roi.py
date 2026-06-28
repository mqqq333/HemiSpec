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

        for label in labels:
            values = data[atlas == label]
            values = values[np.isfinite(values)]
            if config.ignore_zero:
                values = values[values != 0]
            if values.size == 0:
                value = np.nan
            elif config.stat == "mean":
                value = float(np.mean(values))
            elif config.stat == "median":
                value = float(np.median(values))
            else:
                raise ValueError("ROI stat must be one of: mean, median")
            rows.append(
                {
                    **meta,
                    "atlas": config.atlas_path.stem,
                    "roi_label": label,
                    "roi_name": label_names.get(label, ""),
                    "stat": config.stat,
                    "value": value,
                    "n_voxels": int(values.size),
                    "map_path": str(map_path),
                }
            )

    df = pd.DataFrame(rows)
    config.out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(config.out_csv, index=False)
    return df


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
