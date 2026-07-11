# Quick start

The current public v0.1.0 release is available from GitHub Releases and source checkouts. The PyPI project is not public yet.

!!! note "Command naming"
    Use `hemispec` for the command-line interface and `hemispec-gui` for the graphical interface.

## 1. Run the public-safe synthetic smoke test

Download `hemispec_toolkit-0.1.0-py3-none-any.whl` from the GitHub Release, then run:

```bash
python -m pip install ./hemispec_toolkit-0.1.0-py3-none-any.whl
hemispec --help
hemispec quickstart --out-dir hemispec_quickstart
```

The generated data are synthetic and are not anatomical results. Use this command only to validate installation and public file/command contracts.

## 2. Install a model-enabled source checkout

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e .[gui,model,classifier]
hemispec models --install --with-classifier  # optional cache pre-download
```

PyTorch must be installed in the active environment. The released DGN and classifier bundles can be read from the Git-LFS checkout or downloaded into the user cache.

## 3. Prepare DGN-ready gray-matter maps

Raw T1-weighted MRI is **not** a valid input to `hemispec workflow`. From a source checkout, run the study FSL preprocessing script:

```bash
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
  --out-dir outputs/hemispec_workflow
```

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

Use an approved atlas and compatible label table:

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_workflow \
  --roi-atlas /approved/path/atlas.nii.gz \
  --roi-label-table /approved/path/labels.xlsx
```

For voxel maps only:

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_workflow \
  --no-roi-table
```

## 7. Optional validation

Hemisphere classification and TRT are opt-in:

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_workflow \
  --run-classifier \
  --run-trt
```

Classifier validation requires ROI features. TRT requires filenames matching the configured session pattern.

To run standalone validation commands later, keep intermediates:

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_workflow \
  --keep-intermediate

hemispec trt \
  --maps-dir outputs/hemispec_workflow/intermediate/combined_maps \
  --out-dir outputs/trt_validation
```

## Current boundaries

- There is no standalone `report` command.
- There is no standalone `roi` command.
- Real subject MRI, unpublished cohort results, and manuscript-draft figures are not public examples.
- Atlas files require documented source and redistribution approval.
- The behavioral-phenotype tutorial remains a roadmap page rather than a complete reproduction workflow.
