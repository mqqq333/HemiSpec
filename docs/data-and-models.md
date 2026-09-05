# Data and models

!!! important "MRI input is a separate prerequisite"
    Model weights and atlas files do not convert raw T1 MRI into DGN input. Prepare one MNI152 1.5 mm `*_GM_masked.nii.gz` file per subject first; see [Input and preprocessing](input-preprocessing.md).

Current `main` uses two DGN generator checkpoints, optional hemisphere-classifier bundles, and an optional atlas/label table for ROI export.

## Recommended local model assets

Use a current source checkout with Git LFS:

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e ".[model,classifier]"
git rev-parse HEAD
```

The DGN checkpoints and classifier bundles are then available under `assets/models/`. Record the commit hash printed by `git rev-parse HEAD` so the code and model checkout can be identified later. Explicit CLI/API paths or `HEMISPEC_DGN_MODEL_ROOT` and `HEMISPEC_CLASSIFIER_MODEL_DIR` can select another approved local bundle.

## Current cache-download boundary

Current `main` can download missing DGN checkpoints into the per-user cache from files tracked by Git LFS on the repository's `main` branch. These downloads come from GitHub's media endpoint, not from the archived `v0.1.0` GitHub Release assets. The current classifier cache download is incomplete because its required `feature_names.csv` media URLs return HTTP 404; use the classifier files from a Git-LFS checkout or an explicit local classifier directory instead. Downloaded DGN files are stored under `HEMISPEC_MODEL_CACHE` when set, otherwise under the platform-specific user cache.

The archived `v0.1.0` wheel does not contain the current model downloader. The PyPI project is not public, so `pip install hemispec-toolkit` is not a current installation instruction.

## Atlas files for ROI export

ROI export is optional and requires:

1. a parcellation atlas NIfTI on the same grid and affine as the HemiSpec maps;
2. a compatible label table.

The repository contains only an atlas manifest/template and placement documentation. The Glasser NIfTI and label table are not distributed in the public source branch because source, license, checksum, and redistribution approval must be documented first.

Place an approved local bundle at:

```text
assets/atlases/glasser/MNI_Glasser_HCP_v1.0_1p5mm.nii.gz
assets/atlases/glasser/Glasser_label_index_mapping.xlsx
```

or configure explicit paths:

```bash
export HEMISPEC_GLASSER_ATLAS=/approved/path/atlas.nii.gz
export HEMISPEC_GLASSER_LABEL_TABLE=/approved/path/labels.xlsx
```

Without an atlas, the workflow can still generate voxel-wise ANS/RNS maps by using `--no-roi-table`.

## What is not distributed

The public branch must not contain raw or subject-level MRI, generated study outputs, unpublished cohort results, manuscript-draft figures, or atlas files without documented redistribution approval.

## Attribution

The cross-hemispheric DGN and ANS/RNS framework originate from Wang et al. (2024). For Glasser/HCP-MMP atlas use, also cite Glasser et al. (2016), separately from the provenance of the derived MNI NIfTI conversion; see [Citation](citation.md). Model and atlas bundles require their own provenance, checksum, compatibility, and license records.
