from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .similarity import SpecificityResult


def save_specificity_result(result: SpecificityResult, out_dir: str | Path, label: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    matrix_path = out / f"similarity_{label}.csv"
    np.savetxt(matrix_path, result.matrix, delimiter=",", fmt="%.6f")

    pd.DataFrame(
        {
            "subject": result.subjects,
            "within_similarity": result.within,
        }
    ).to_csv(out / f"within_{label}.csv", index=False)

    summary = out / f"summary_{label}.txt"
    with summary.open("w", encoding="utf-8") as f:
        f.write(f"{label}\n")
        f.write(f"metric kind = {result.kind}\n")
        f.write(f"hemisphere/ROI = {result.hemi}\n")
        f.write(f"N subjects = {len(result.subjects)}\n")
        f.write(f"mask voxels = {result.n_voxels}\n")
        f.write(f"top-1 match rate = {result.match_rate:.2f}%\n")
        f.write(f"specificity index (within - between) = {result.specificity_index:.6f}\n")
        f.write(f"Cohen d (within vs between) = {result.cohen_d:.6f}\n")
        f.write(
            "within similarity: "
            f"mean={result.within.mean():.6f}, std={result.within.std(ddof=1):.6f}, "
            f"n={len(result.within)}\n"
        )
        f.write(
            "between similarity: "
            f"mean={result.between.mean():.6f}, std={result.between.std(ddof=1):.6f}, "
            f"n={len(result.between)}\n"
        )
        f.write(f"Welch t-test: t={result.t_value:.6f}, p={result.p_value:.6e}\n")

