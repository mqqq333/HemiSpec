# GUI user guide

The package-installed `hemispec-gui` command launches the standard HemiSpec bilateral workflow. Start it from the same Python environment that contains HemiSpec and PyTorch.

## Launch

Install the current GUI from a Git LFS source checkout of `main`:

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e ".[gui,model,classifier]"
git rev-parse HEAD
hemispec-gui
```

Record the printed commit hash with the analysis. The PyPI project is not public, and this guide does not use the archived v0.1.0 wheel. Older versions remain available on the [GitHub Releases page](https://github.com/mqqq333/HemiSpec/releases).

## Before opening the GUI

Prepare one DGN-ready GM map per subject. Raw T1-weighted images must first pass through the documented FSL preprocessing workflow:

```text
T1-weighted NIfTI -> process_single_subject.sh -> *_GM_masked.nii.gz
```

See [Input and preprocessing](../input-preprocessing.md).

## Six GUI cards

### 1. Input GM maps

Select a directory or enter a glob such as:

```text
derivatives/*_GM_masked.nii.gz
```

### 2. Output workspace

Choose a new, empty output directory for each run. Final maps are written under `voxel_maps/`; tables and optional validation outputs use their own subdirectories.

### 3. Setup status

Confirm that PyTorch and both DGN directions are available. Atlas and classifier rows are optional unless their corresponding options are enabled.

### 4. Optional ROI table

Enable ROI export only when an atlas and compatible label table are available. The atlas must share the input-map grid and affine. A custom atlas is valid for ROI-only export. The released classifier instead requires its compatible Glasser 1.5 mm atlas, with labels `1..180` on the left and `1001..1180` on the right.

### 5. Optional validation

- **Hemisphere-classifier validation** requires the compatible Glasser ROI features and a local classifier bundle from the Git LFS checkout. Current classifier cache download is incomplete; see [Data and models](../data-and-models.md#current-cache-download-boundary).
- **TRT reliability** requires at least two subjects with two scans each. The GUI uses its encapsulated default pattern, such as `sub-MSC001_run-01_GM_masked.nii.gz` and `sub-MSC001_run-02_GM_masked.nii.gz`; use the CLI when filenames such as `sub-001_run-01_GM_masked.nii.gz` require explicit regex/session flags.
- **Keep intermediate outputs** preserves reconstructions and direction-specific maps for debugging, plus `intermediate/combined_maps/` for later standalone validation. Direction-specific maps use a different suffix contract.

### 6. Run controls

Review or copy the equivalent CLI command, start or stop the workflow, inspect logs, and open the output directory.

## Reproducibility

Copy the displayed CLI command into the study record together with the HemiSpec commit/version, preprocessing script version, model bundle, atlas version, and enabled optional validation steps.

ANS/RNS and the cross-hemispheric DGN framework originate from Wang et al. (2024); see [Citation](../citation.md).
