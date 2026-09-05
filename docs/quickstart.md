# Quick start

These commands target the current `main` source checkout, not the archived `v0.1.0` wheel. The PyPI project is not public yet. See [Installation](installation.md) for the release boundary.

!!! note "Command naming"
    Use `hemispec` for the command-line interface and `hemispec-gui` for the graphical interface.

## 1. Install the current source checkout

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e ".[gui,model,classifier]"
git rev-parse HEAD
hemispec models
hemispec --help
```

PyTorch must be installed in the active environment. Keep the Git commit with your run record. `git lfs pull` must retrieve the actual DGN and classifier files. Use these local classifier bundles; the current classifier-cache download has a known CSV URL issue described in [Data and models](data-and-models.md).

## 2. Run the synthetic smoke test

From the installed source checkout:

```bash
hemispec quickstart --out-dir hemispec_quickstart
```

The generated data are synthetic and are not anatomical results. This checks installation and file/command contracts without running model inference. Use a new or empty output directory; `--force` currently deletes the whole selected directory, including unrelated files.

## 3. Prepare DGN-ready gray-matter maps

Raw T1-weighted MRI is **not** a valid input to `hemispec workflow`. From a source checkout, run the study FSL preprocessing script:

```bash
mkdir -p derivatives
bash process_single_subject.sh \
  raw/sub-001_T1w.nii.gz \
  derivatives/sub-001
```

Expected DGN input:

```text
derivatives/sub-001_GM_masked.nii.gz
```

Before inference, verify the `121 × 145 × 121` grid, `1.5 mm` voxel size, affine, finite `0–1` GM values, registration, segmentation, and mask quality. See [Input and preprocessing](input-preprocessing.md).

## 4. Run the standard bilateral workflow

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_workflow \
  --no-roi-table
```

This first run produces voxel maps and the subject summary without requiring an atlas. Use a new output directory for every run, including retries and different input subsets, to avoid mixing current and earlier outputs.

The primary outputs are:

```text
outputs/hemispec_workflow/
├── voxel_maps/     # ANS.L, ANS.R, RNS.L, RNS.R per subject
├── tables/         # subject summary and optional ROI tables
└── validation/     # optional classifier/TRT outputs
```

ANS/RNS and the cross-hemispheric DGN framework originate from Wang et al. (2024); see [ANS and RNS metrics](methods/ans-rns-metrics.md).

## 5. Launch the GUI

```bash
hemispec-gui
```

The GUI reports PyTorch, DGN, atlas, and classifier readiness. Users choose the GM input glob, output workspace, optional ROI export, optional hemisphere-classifier validation, optional TRT reliability, and whether to retain intermediates. See the [GUI user guide](developer/gui-user-guide.md).

## 6. Optional ROI table

Use an approved atlas on the same grid as the GM maps and a compatible label table. Custom atlases are supported for ROI summaries, but are not interchangeable with the atlas used to train the released classifier:

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_roi \
  --roi-atlas /approved/path/atlas.nii.gz \
  --roi-label-table /approved/path/labels.xlsx
```

## 7. Optional validation

### Hemisphere classification

The released classifier requires the compatible Glasser atlas: 180 homologous parcels per hemisphere, with left labels `1–180` and right labels `1001–1180`, on the same 1.5 mm grid. The atlas is not distributed in the public checkout; obtain it and its label table as described in [Data and models](data-and-models.md). Label numbers alone do not establish anatomical compatibility.

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_classifier \
  --roi-atlas /approved/path/glasser_1p5mm.nii.gz \
  --roi-label-table /approved/path/glasser_labels.csv \
  --classifier-model-dir assets/models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models \
  --run-classifier
```

### Test-retest reliability

TRT needs two scans from each of at least two subjects. For example, prepare a separate input directory containing:

```text
derivatives_trt/
  sub-001_run-01_GM_masked.nii.gz
  sub-001_run-02_GM_masked.nii.gz
  sub-002_run-01_GM_masked.nii.gz
  sub-002_run-02_GM_masked.nii.gz
```

Use an explicit subject/session pattern for these names. Retaining intermediates also permits later standalone validation:

```bash
hemispec workflow \
  --input-glob "derivatives_trt/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_trt \
  --no-roi-table \
  --keep-intermediate \
  --run-trt \
  --trt-file-regex '(?P<subject>sub-[0-9]+)_(?P<session>run-[0-9]+)' \
  --trt-session-a run-01 \
  --trt-session-b run-02

hemispec trt \
  --maps-dir outputs/hemispec_trt/intermediate/combined_maps \
  --out-dir outputs/trt_validation \
  --file-regex '(?P<subject>sub-[0-9]+)_(?P<session>run-[0-9]+)' \
  --session-a run-01 \
  --session-b run-02
```

## Current boundaries

- There is no standalone `report` command.
- There is no standalone `roi` command.
- Real subject MRI, unpublished cohort results, and manuscript-draft figures are not public examples.
- Atlas files require documented source and redistribution approval.
- The behavioral-phenotype tutorial remains a roadmap page rather than a complete reproduction workflow.
