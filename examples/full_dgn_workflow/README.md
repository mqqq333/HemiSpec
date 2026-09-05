# Full DGN workflow example

This example uses the released DGN and hemisphere-classifier files tracked in the current source checkout with Git LFS. It does not download models and does not include MRI inputs or the separately licensed Glasser atlas.

## Prepare the checkout

```bash
git lfs install
git lfs pull
python -m pip install -e .[model,classifier]
```

Use these local model paths:

```text
assets/models/dgn/
assets/models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models/
```

Provide a compatible MNI Glasser 1.5 mm atlas and label table at the documented local locations (or equivalent explicit paths):

```text
assets/atlases/glasser/MNI_Glasser_HCP_v1.0_1p5mm.nii.gz
assets/atlases/glasser/Glasser_label_index_mapping.xlsx
```

The released classifier requires exactly 180 left-hemisphere labels `1..180` and 180 right-hemisphere labels `1001..1180` on the canonical grid. A custom atlas may be used for ROI-only export, but must not be combined with the released classifier.

## Repeated-scan inputs

TRT requires at least two subjects with both sessions. For example:

```text
derivatives/
  sub-001_ses-01_GM_masked.nii.gz
  sub-001_ses-02_GM_masked.nii.gz
  sub-002_ses-01_GM_masked.nii.gz
  sub-002_ses-02_GM_masked.nii.gz
```

Before running, verify every image against the canonical FSL MNI152 1.5 mm grid, including shape, voxel size, orientation, and full affine. See [`docs/input-preprocessing.md`](../../docs/input-preprocessing.md).

## Bilateral workflow with classifier and TRT

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --model-root "assets/models/dgn" \
  --out-dir "outputs/hemispec_full_ses01_ses02" \
  --roi-atlas "assets/atlases/glasser/MNI_Glasser_HCP_v1.0_1p5mm.nii.gz" \
  --roi-label-table "assets/atlases/glasser/Glasser_label_index_mapping.xlsx" \
  --run-classifier \
  --classifier-model-dir "assets/models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models" \
  --run-trt \
  --trt-file-regex "(?P<subject>sub-[^_]+)_(?P<session>ses-[^_]+)_" \
  --trt-session-a ses-01 \
  --trt-session-b ses-02 \
  --keep-intermediate
```

`--keep-intermediate` retains `intermediate/combined_maps`, including names such as `sub-001_ses-01_ANS.nii.gz` and `sub-002_ses-02_RNS.nii.gz`, so the pairing can be audited. Use a fresh `--out-dir`, such as `outputs/hemispec_full_ses01_ses03`, for a different session pair or parameter variant.

For a no-model smoke test, use `examples/synthetic_quickstart/`.
