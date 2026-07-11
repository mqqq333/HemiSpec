# Data and models

!!! important "MRI input is a separate prerequisite"
    Model weights and atlas files do not convert raw T1 MRI into DGN input. Prepare one MNI152 1.5 mm `*_GM_masked.nii.gz` file per subject first; see [Input and preprocessing](input-preprocessing.md).

HemiSpec model-enabled workflows use two DGN generator checkpoints, optional hemisphere-classifier bundles, and an optional atlas/label table for ROI export.

## DGN and classifier model bundles

### Source checkout with Git LFS

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e .[model,classifier]
```

### Release wheel or lightweight install

The Python wheel does not embed the 300 MB+ model bundles. After installing the v0.1.0 wheel, HemiSpec can download the released defaults from the GitHub Release into the per-user cache:

```bash
python -m pip install "./hemispec_toolkit-0.1.0-py3-none-any.whl[model,classifier]"
hemispec models --install --with-classifier
```

The PyPI project is not public yet. Do not use `pip install hemispec-toolkit` as a current installation instruction.

Downloaded files are stored under `HEMISPEC_MODEL_CACHE` when set, otherwise under the platform-specific user cache. Explicit environment variables or CLI/API paths can override the defaults.

## Atlas files for ROI export

ROI export is optional and requires:

1. a parcellation atlas NIfTI on the same grid and affine as the HemiSpec maps;
2. a compatible label table.

The repository contains only an atlas manifest/template and placement documentation. The Glasser NIfTI and label table are **not distributed in the public source branch** because source, license, checksum, and redistribution approval must be documented first.

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

A custom atlas can be passed directly:

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/ \
  --roi-atlas /approved/path/atlas.nii.gz \
  --roi-label-table /approved/path/labels.xlsx
```

Without an atlas, the workflow can still generate voxel-wise ANS/RNS maps by using `--no-roi-table`.

## What is not distributed

The public branch must not contain raw or subject-level MRI, generated study outputs, unpublished cohort results, manuscript-draft figures, or atlas files without documented redistribution approval. Use the synthetic quickstart for public examples.

## Attribution

The cross-hemispheric DGN and ANS/RNS framework originate from Wang et al. (2024); see [Citation](citation.md). Model and atlas bundles require their own provenance, checksum, compatibility, and license records.
