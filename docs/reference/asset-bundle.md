# External asset bundles

Current HemiSpec `main` includes reusable DGN checkpoints and hemisphere-classifier bundles under `assets/models/` via Git LFS. Large model binaries remain outside the wheel. The current source code supports DGN checkpoint downloads into the user cache, but classifier assets require a Git-LFS checkout or explicit local directory because the classifier cache download is incomplete. The archived `v0.1.0` wheel does not include this downloader, and the PyPI project is not public yet. External asset bundles remain useful for offline installs, custom model bundles, atlas payloads, approved sample data, or compiled app distributions.

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

`ASSET_MANIFEST.yml` should record enough information for another lab to decide whether the bundle is compatible with their workflow. This is a template, not a published compatibility claim; replace the example metadata with tested values:

```yaml
asset_bundle: HemiSpec-Assets
version: 0.1.0
date: 2026-06-29
compatible_with:
  package: hemispec-toolkit
  version: <tested package version>
  commit: <tested HemiSpec commit>
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

Resolution order is explicit CLI/GUI paths first, then environment variables, then local repository conventions, then the per-user cache. `HEMISPEC_MODEL_CACHE`, `HEMISPEC_MODEL_ASSET_BASE_URL`, `HEMISPEC_AUTO_DOWNLOAD_MODELS`, and `HEMISPEC_DISABLE_MODEL_AUTO_DOWNLOAD` control the built-in model cache/download path.

## Release checklist

Before distributing an asset bundle, verify:

- no raw or subject-identifying MRI data are included unless explicitly cleared for redistribution;
- every model, atlas, classifier, and label table has a checksum in `SHA256SUMS.txt`;
- license and citation requirements are present in `LICENSES/` or the manifest;
- preprocessing assumptions and compatible HemiSpec versions are stated;
- the bundle works with the current `main` source checkout, recording `git rev-parse HEAD`; the archived `v0.1.0` artifacts are historical and are not the current compatibility target;
- the bundle is published through an explicit release channel such as GitHub Releases, Zenodo, OSF, or institutional storage.

## Runtime boundary

The lightweight Windows CLI/GUI artifacts do not bundle PyTorch, atlas payloads, real MRI inputs, or generated outputs. Model-enabled workflows require a Python environment with PyTorch. In current `main`, DGN checkpoints can come from a Git-LFS source checkout, the per-user auto-download cache, or an explicitly configured offline asset bundle. Classifier assets require a Git-LFS checkout or explicit local directory; see the current download limitation in [Data and models](../data-and-models.md).

## Related pages

- [Data and models](../data-and-models.md)
- [Release artifacts](../release-artifacts.md)
- [v0.1.0 release verification](../developer/release-verification-v0.1.0.md)
- [Roadmap](../developer/roadmap.md)
