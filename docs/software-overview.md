# Software overview

HemiSpec is organized as a PyPI-first software ecosystem rather than a source-only repository. The Python package is the primary artifact; the CLI, GUI entry point, and compiled desktop folders are built from the same public API.

<figure markdown="span">
  ![HemiSpec workflow overview](assets/figures/hemispec-workflow-overview-ai.png){ width="100%" }
  <figcaption>HemiSpec follows the public workflow sequence from Input GM to Reconstruction, Difference analysis, and Hemisphere-specific metrics, then extends those outputs into ROI tables, validation, and release artifacts.</figcaption>
</figure>

## User-facing layers

| Layer | Public name | Status | Purpose |
| --- | --- | --- | --- |
| Python package | `hemispec-toolkit` | Primary public artifact | Installable API plus CLI/GUI entry points in the active Python/PyTorch environment. |
| CLI | `hemispec` | PyPI-installed entry point | Scriptable workflows for servers and clusters. |
| GUI | `hemispec-gui` | PyPI-installed entry point | Desktop launcher for ANS/RNS generation, optional ROI tables, and optional validation, run from the same environment as PyTorch. |
| Compiled app | HemiSpec Desktop / HemiSpec Model App | Fallback release target | Folder distributions for users who cannot manage Python environments. |

<figure markdown="span">
  ![HemiSpec GUI preview](assets/figures/hemispec-gui-preview.png){ width="100%" }
  <figcaption>Current compact GUI preview with public-safe placeholder paths. The GUI is a thin launcher over `hemispec workflow`.</figcaption>
</figure>

## Current GUI scope

The default GUI is intentionally narrow. It exposes the decisions normal users need to obtain ANS/RNS maps:

- preprocessed GM input glob,
- output workspace,
- optional ROI table export with atlas and label table paths,
- optional hemisphere-classifier validation,
- optional TRT reliability,
- run/open/copy-CLI/log controls.

It does not expose model checkpoints, device selection, thresholds, suffix rules, classifier bundle paths, or TRT regexes. Those advanced settings remain available through the CLI/API so that the GUI remains reproducible and easy to maintain.

## Current PyPI-first release split

- **PyPI package:** CLI, compact GUI launcher, compute, ROI export, validation, and inspection without bundling private model/data assets.
- **Model-enabled PyPI environment:** end-to-end DGN inference plus ANS/RNS workflows using released DGN/classifier defaults from Git LFS, first-run cache download, or explicit offline assets; atlas files remain optional for ROI export.

The default public build should avoid silently bundling private `assets/`; model and atlas bundles should be explicit release artifacts with checksums, license notes, and compatibility metadata. Compiled apps remain fallback variants rather than the primary distribution path.
