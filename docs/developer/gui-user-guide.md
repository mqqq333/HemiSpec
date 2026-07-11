# GUI user guide

The package-installed `hemispec-gui` command launches the standard HemiSpec bilateral workflow. Start it from the same Python environment that contains HemiSpec and PyTorch.

## Launch

From a source checkout:

```bash
python -m pip install -e .[gui,model,classifier]
hemispec-gui
```

From the v0.1.0 release wheel:

```bash
python -m pip install "./hemispec_toolkit-0.1.0-py3-none-any.whl[gui,model,classifier]"
hemispec-gui
```

The PyPI project is not yet public; use the GitHub Release wheel or a source checkout.

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

Choose a new or existing output directory. Final maps are written under `voxel_maps/`; tables and optional validation outputs use their own subdirectories.

### 3. Setup status

Confirm that PyTorch and both DGN directions are available. Atlas and classifier rows are optional unless their corresponding options are enabled.

### 4. Optional ROI table

Enable ROI export only when an atlas and compatible label table are available. The atlas must share the input-map grid and affine.

### 5. Optional validation

- **Hemisphere-classifier validation** requires ROI features and remains optional.
- **TRT reliability** requires filenames that match the configured session pattern.
- **Keep intermediate outputs** preserves reconstructions and direction-specific maps for debugging or standalone validation.

### 6. Run controls

Review or copy the equivalent CLI command, start or stop the workflow, inspect logs, and open the output directory.

## Reproducibility

Copy the displayed CLI command into the study record together with the HemiSpec commit/version, preprocessing script version, model bundle, atlas version, and enabled optional validation steps.

ANS/RNS and the cross-hemispheric DGN framework originate from Wang et al. (2024); see [Citation](../citation.md).
