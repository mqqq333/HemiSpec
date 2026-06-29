# Full DGN workflow example contract

This directory is a placeholder for a future public model-enabled HemiSpec demo. It intentionally contains no model weights, atlas payloads, classifier bundles, real MRI inputs, or generated outputs.

Use it as the expected file/command contract when an approved `HemiSpec-Assets` bundle and approved preprocessed sample data become available.

## Expected assets

```text
HemiSpec-Assets/
  ASSET_MANIFEST.yml
  SHA256SUMS.txt
  LICENSES/
  models/dgn/
  models/hemisphere_classifier/
  atlases/glasser/
```

## Expected inputs

```text
derivatives/
  sub-001_GM_masked.nii.gz
  sub-002_GM_masked.nii.gz
```

## Example command

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --model-root "$HEMISPEC_DGN_MODEL_ROOT" \
  --out-dir outputs/hemispec_full_demo \
  --roi-atlas "$HEMISPEC_GLASSER_ATLAS" \
  --roi-label-table "$HEMISPEC_GLASSER_LABEL_TABLE" \
  --run-classifier \
  --classifier-model-dir "$HEMISPEC_CLASSIFIER_MODEL_DIR" \
  --run-trt
```

For a current no-asset smoke test, use `examples/synthetic_quickstart/` instead.
