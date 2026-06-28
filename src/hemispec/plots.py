from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


def plot_heatmap(matrix: np.ndarray, out_png: str | Path, title: str, flip_diag: bool = True) -> None:
    display = np.flipud(matrix) if flip_diag else matrix
    fig, ax = plt.subplots(figsize=(3.2, 3.0))
    im = ax.imshow(display, cmap="YlOrRd", vmin=0.0, vmax=1.0, interpolation="nearest")
    ax.set_title(title, fontsize=10)
    ax.set_xticks([])
    ax.set_yticks([])
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("Similarity", rotation=270, labelpad=10)
    fig.tight_layout()
    fig.savefig(out_png, dpi=300)
    plt.close(fig)


def plot_within_between_box(
    within: np.ndarray,
    between: np.ndarray,
    out_png: str | Path,
    title: str,
) -> None:
    fig, ax = plt.subplots(figsize=(3.1, 3.0))
    ax.boxplot([within, between], labels=["Within", "Between"], showfliers=False)
    ax.set_ylabel("Similarity")
    ax.set_title(title, fontsize=10)
    fig.tight_layout()
    fig.savefig(out_png, dpi=300)
    plt.close(fig)

