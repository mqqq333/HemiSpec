# HemiSpec assets

Large local assets are intentionally not tracked in git.

This directory is the default local lookup root for optional resources such as:

- trained DGN model bundles,
- hemisphere-classifier bundles,
- atlas files and label tables,
- small synthetic/example fixtures once approved for release.

Before a public release, document each asset with its version, license, checksum,
preprocessing assumptions, and download location. Use GitHub Releases, Zenodo/OSF,
or another explicit distribution channel instead of committing large weights or
neuroimaging files directly to the source repository.

The local Glasser atlas bundle is expected under `assets/atlases/glasser/`; see that directory for the manifest template.


## Recommended external bundle layout

```text
HemiSpec-Assets/
  ASSET_MANIFEST.yml
  SHA256SUMS.txt
  LICENSES/
  models/dgn/
  models/hemisphere_classifier/
  atlases/glasser/
```

Keep this bundle outside the source repository unless a release explicitly approves a small manifest/readme. Configure local runs with `HEMISPEC_ASSET_ROOT`, `HEMISPEC_DGN_MODEL_ROOT`, `HEMISPEC_CLASSIFIER_MODEL_DIR`, `HEMISPEC_GLASSER_ATLAS`, and `HEMISPEC_GLASSER_LABEL_TABLE`, or pass explicit CLI/GUI paths.
