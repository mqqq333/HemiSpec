# Data and models

HemiSpec works with neuroimaging data and trained model weights, so the public repository uses conservative data boundaries.

## Do not commit

- Raw T1-weighted MRI data.
- Subject-level derivatives that are not cleared for public redistribution.
- Large `.nii.gz`, `.pth`, `.pt`, `.ckpt`, `.joblib`, `.pkl`, or `.xlsx` payloads unless they are explicitly approved release artifacts and intentionally tracked.
- Manuscript-only figures or tables before public release approval.
- Private workstation paths, server paths, keys, tokens, or local-only coordination notes.

## Repository policy

The source repository contains code, documentation, tests, synthetic examples, and approved reusable model bundles. Large binary model files under `assets/models/` are tracked with Git LFS:

```text
assets/models/dgn/                       # reusable bilateral DGN generator checkpoints
assets/models/hemisphere_classifier/     # reusable classifier bundles
assets/atlases/                          # atlas payloads may be local/external unless explicitly released
```

The package wheel and default PyInstaller specs remain lightweight and do not embed repository-level `assets/`. Instead, model-enabled CLI/GUI/API runs can download the released model files from the GitHub repository into a per-user cache when the local checkout/cache is empty.

## Bundled model layout

A Git-LFS source checkout provides this model layout:

```text
assets/models/dgn/
  outputs_bi_stable_L/ckpts/best_netG_L.pth
  outputs_bi_stable_R/ckpts/best_netG_R.pth
assets/models/hemisphere_classifier/
  OUT_noICBM_train_ICBM_external_saved_models/
  OUT_noICBM_train_ICBM_external_saved_models_paired_residual/
```

Clone with `git lfs install` and `git lfs pull`; otherwise these files may appear as small LFS pointer text files instead of usable model binaries.

Supported environment variables:

```text
HEMISPEC_ASSET_ROOT
HEMISPEC_DGN_MODEL_ROOT
HEMISPEC_CLASSIFIER_MODEL_DIR
HEMISPEC_MODEL_CACHE
HEMISPEC_MODEL_ASSET_BASE_URL
HEMISPEC_AUTO_DOWNLOAD_MODELS
HEMISPEC_DISABLE_MODEL_AUTO_DOWNLOAD
HEMISPEC_GLASSER_ATLAS
HEMISPEC_GLASSER_LABEL_TABLE
```

The GUI and CLI resolve explicit paths first, then environment variables, then local repository conventions, then the per-user cache. That means a source checkout normally finds `assets/models/dgn` and the default classifier bundle without extra flags; a wheel/PyPI install downloads the released defaults into `HEMISPEC_MODEL_CACHE` (or the OS-specific HemiSpec cache) on first model use. See [External asset bundles](reference/asset-bundle.md) for the manifest/checksum/license contract when distributing additional assets.

## External release channels

Prefer GitHub Releases, Zenodo, OSF, or institutional storage for model weights and compiled-app asset bundles. Every released asset bundle should include:

- version and date,
- source/provenance,
- license and citation requirements,
- expected local path or environment variable,
- checksums,
- preprocessing assumptions,
- compatible `hemispec-toolkit` version.

## Method and model attribution

If a release distributes or documents ANS/RNS-capable models or workflows, keep the method boundary explicit: the original ANS/RNS metrics and cross-hemispheric DGN framework come from Wang et al. 2024, *Patterns*. HemiSpec packages and extends that workflow for the current software and handedness application.
