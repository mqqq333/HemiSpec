# Data and models

HemiSpec works with neuroimaging data and trained model weights, so the public repository needs conservative data boundaries.

## Do not commit

- Raw T1-weighted MRI data.
- Subject-level derivatives that are not cleared for public redistribution.
- Large `.nii.gz`, `.pth`, `.joblib`, or `.pkl` files unless they are explicitly approved release artifacts.
- Manuscript-only figures or tables before public release approval.
- Private workstation paths or local-only coordination notes.

## Prefer

- Synthetic or license-safe demo inputs.
- Small derived examples with clear provenance.
- GitHub Releases, Zenodo, OSF, or institutional storage for model weights and compiled-app asset bundles.
- A model bundle manifest that can be public even if weights are hosted separately.

## Local development sources

Keep local machine-specific paths in ignored private notes, not in public documentation. Public docs should refer to placeholders such as:

```text
<local-toolkit-checkout>
<analysis-workspace>
<planning-workspace>
```

These placeholders are not part of the public release contract.
## Method and model attribution

If a release distributes or documents ANS/RNS-capable models or workflows, keep
the method boundary explicit: the original ANS/RNS metrics and cross-hemispheric
DGN framework come from Wang et al. 2024, *Patterns*. HemiSpec packages and
extends that workflow for the current software and handedness application.
