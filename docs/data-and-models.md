# Data and models

HemiSpec needs two types of external assets to run model-enabled workflows: **DGN model weights** and an **atlas file** for ROI export. Neither is bundled in the Python wheel or the lightweight desktop app.

## Model weights

HemiSpec uses two trained DGN generator checkpoints (one per hemisphere direction) and optional hemisphere-classifier bundles.

**Source checkout (Git LFS)**

Clone with LFS enabled to get the model files directly:

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
```

**Wheel / PyPI install**

Models are downloaded automatically on the first model-enabled run:

```bash
python -m pip install "hemispec-toolkit[model,classifier]"
hemispec workflow --input-glob "derivatives/*_GM_masked.nii.gz" --out-dir outputs/
```

To pre-download explicitly:

```bash
hemispec models --install --with-classifier
```

Downloaded files are stored in the HemiSpec user cache (`HEMISPEC_MODEL_CACHE`, or the OS default cache directory).

## Atlas file

ROI table export requires a parcellation atlas in MNI space. HemiSpec includes a Glasser HCP-MMP atlas in the repository as a ready-to-use default. You can also use any compatible atlas in the same format.

**Download the bundled Glasser atlas**

The atlas files are included in the repository under `assets/atlases/glasser/`. With a source checkout they are available directly. You can also download them individually from GitHub:

- [`MNI_Glasser_HCP_v1.0_1p5mm.nii.gz`](https://github.com/mqqq333/HemiSpec/raw/main/assets/atlases/glasser/MNI_Glasser_HCP_v1.0_1p5mm.nii.gz)
- [`Glasser_label_index_mapping.xlsx`](https://github.com/mqqq333/HemiSpec/raw/main/assets/atlases/glasser/Glasser_label_index_mapping.xlsx)

Set the paths once via environment variables:

```bash
export HEMISPEC_GLASSER_ATLAS=/path/to/MNI_Glasser_HCP_v1.0_1p5mm.nii.gz
export HEMISPEC_GLASSER_LABEL_TABLE=/path/to/Glasser_label_index_mapping.xlsx
```

**Use a custom atlas**

Pass any NIfTI atlas and label table directly:

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/ \
  --roi-atlas /path/to/atlas.nii.gz \
  --roi-label-table /path/to/labels.xlsx
```

ROI export is optional. If no atlas is provided, voxel-wise ANS/RNS maps are still produced.

## What is not distributed

Real MRI data and generated outputs are never distributed with HemiSpec. The public repository contains only code, documentation, tests, synthetic examples, and the approved reusable model bundles under Git LFS.

## Attribution

The ANS/RNS metrics and cross-hemispheric DGN framework originate from Wang et al. 2024, *Patterns*. HemiSpec packages and extends that workflow.
