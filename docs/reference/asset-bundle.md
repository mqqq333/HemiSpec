# External asset bundles

HemiSpec source releases are lightweight. DGN weights, atlas payloads, hemisphere-classifier bundles, real MRI inputs, and generated outputs are distributed separately as external assets.

## Recommended layout

```text
HemiSpec-Assets/
  ASSET_MANIFEST.yml
  SHA256SUMS.txt
  LICENSES/
  models/
    dgn/
      <left-to-right-bundle>/ckpts/<checkpoint-name>.pth
      <right-to-left-bundle>/ckpts/<checkpoint-name>.pth
    hemisphere_classifier/
      <classifier-bundle>/
  atlases/
    glasser/
      <glasser-atlas>.nii.gz
      <glasser-label-table>.xlsx
```

## Manifest contract

`ASSET_MANIFEST.yml` should record enough information for another lab to decide whether the bundle is compatible with their workflow:

```yaml
asset_bundle: HemiSpec-Assets
version: 0.1.0
date: 2026-06-29
compatible_with:
  package: hemispec-toolkit
  version: ">=0.1.0,<0.2"
contents:
  dgn_models:
    root: models/dgn
    directions: [L_to_R, R_to_L]
  hemisphere_classifier:
    root: models/hemisphere_classifier
  glasser_atlas:
    atlas: atlases/glasser/<glasser-atlas>.nii.gz
    label_table: atlases/glasser/<glasser-label-table>.xlsx
provenance:
  source: <dataset/training/source summary>
  preprocessing: <required preprocessing assumptions>
license:
  assets: <license or redistribution restriction>
  citations:
    method:
      - Wang et al. 2024, Patterns, https://doi.org/10.1016/j.patter.2024.100930
    assets:
      - <asset-specific citation or DOI>
checksums:
  file: SHA256SUMS.txt
```

## Runtime configuration

Prefer explicit CLI/GUI paths for reproducible runs. Environment variables are useful for local defaults:

```text
HEMISPEC_ASSET_ROOT
HEMISPEC_DGN_MODEL_ROOT
HEMISPEC_CLASSIFIER_MODEL_DIR
HEMISPEC_GLASSER_ATLAS
HEMISPEC_GLASSER_LABEL_TABLE
```

Resolution order is explicit CLI/GUI paths first, then environment variables, then local repository or distribution conventions.

## Release checklist

Before distributing an asset bundle, verify:

- no raw or subject-identifying MRI data are included unless explicitly cleared for redistribution;
- every model, atlas, classifier, and label table has a checksum in `SHA256SUMS.txt`;
- license and citation requirements are present in `LICENSES/` or the manifest;
- preprocessing assumptions and compatible HemiSpec versions are stated;
- the bundle works with the lightweight HemiSpec release downloaded from [https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0](https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0);
- the bundle is published through an explicit release channel such as GitHub Releases, Zenodo, OSF, or institutional storage.

## v0.1.0 boundary

The v0.1.0 Windows CLI/GUI artifacts do not bundle torch, DGN weights, atlas payloads, classifier bundles, real MRI inputs, or generated outputs. Model-enabled workflows require a local Python environment with the optional runtime dependencies and a separately approved asset bundle.

## Related pages

- [Data and models](../data-and-models.md)
- [Release artifacts](../release-artifacts.md)
- [v0.1.0 release verification](../developer/release-verification-v0.1.0.md)
- [Roadmap](../developer/roadmap.md)
