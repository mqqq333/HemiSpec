# Model-enabled DGN workflow

This page documents the public workflow contract for a future model-enabled HemiSpec demo. It is intentionally written as an asset-bundle plan: the source repository and v0.1.0 lightweight desktop artifacts do not ship DGN weights, Glasser atlas payloads, classifier bundles, real MRI inputs, or generated outputs.

## Status

- **Synthetic compute-only demo:** available now; see [Quick start](../quickstart.md).
- **Full DGN demo with public assets:** planned for a separately approved `HemiSpec-Assets` bundle.
- **Private/local smoke tests:** already validated during v0.1.0 preparation, but private model/data payloads are not redistributed.

## Required public assets

A model-enabled demo needs an external asset bundle with this minimum layout:

```text
HemiSpec-Assets/
  ASSET_MANIFEST.yml
  SHA256SUMS.txt
  LICENSES/
  models/dgn/
    <left-to-right-bundle>/ckpts/<checkpoint-name>.pth
    <right-to-left-bundle>/ckpts/<checkpoint-name>.pth
  atlases/glasser/
    <glasser-atlas>.nii.gz
    <glasser-label-table>.xlsx
  models/hemisphere_classifier/
    <classifier-bundle>/
```

The bundle must include provenance, redistribution permission, compatible HemiSpec version, preprocessing assumptions, and checksums. See [External asset bundles](../reference/asset-bundle.md).

## Environment setup

Replace `<version>` with the release you downloaded. Install PyTorch according to your local CPU/GPU environment.

```bash
python -m pip install hemispec_toolkit-<version>-py3-none-any.whl
python -m pip install torch scikit-learn joblib
```

Configure local asset paths explicitly or with environment variables:

```text
HEMISPEC_ASSET_ROOT=/path/to/HemiSpec-Assets
HEMISPEC_DGN_MODEL_ROOT=/path/to/HemiSpec-Assets/models/dgn
HEMISPEC_GLASSER_ATLAS=/path/to/HemiSpec-Assets/atlases/glasser/<glasser-atlas>.nii.gz
HEMISPEC_GLASSER_LABEL_TABLE=/path/to/HemiSpec-Assets/atlases/glasser/<glasser-label-table>.xlsx
HEMISPEC_CLASSIFIER_MODEL_DIR=/path/to/HemiSpec-Assets/models/hemisphere_classifier/<classifier-bundle>
```

## Smoke-test commands

First confirm that HemiSpec can discover model bundles:

```bash
hemispec models --root "$HEMISPEC_DGN_MODEL_ROOT"
```

Then run the standard bilateral workflow on approved preprocessed gray-matter maps:

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

For a first public full demo, use a tiny approved sample dataset and clearly label classifier/TRT outputs as smoke-test connectivity checks rather than model-performance claims.

## GUI path

Start the compact GUI with:

```bash
hemispec-gui
```

The setup status card reports:

- DGN model: found / missing;
- Glasser atlas: found / missing;
- classifier bundle: found / missing;
- PyTorch: available / missing.

Resolve any missing required assets before running an end-to-end DGN workflow. Missing classifier assets only block classifier validation; missing atlas assets only block ROI export and classifier validation.

## Release checklist for the public full demo

Before publishing a full DGN demo bundle:

1. confirm redistribution permission for every model, atlas, classifier, and sample-data file;
2. generate `SHA256SUMS.txt` and verify it after download;
3. document preprocessing assumptions and expected input suffixes;
4. run `hemispec models`, `hemispec workflow`, classifier validation, and TRT on a clean environment;
5. record the validation in a release verification note;
6. keep the asset bundle separate from the source repository.
