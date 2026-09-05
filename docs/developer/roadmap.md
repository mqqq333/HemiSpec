# Roadmap

This page tracks public-facing HemiSpec development after the v0.1.0 first public beta.

## Current status

HemiSpec v0.1.0 was published on 2026-06-28 as a GitHub prerelease: [https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0](https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0). It is research software / public beta, not a mature clinical or commercial product.

The archived release includes the `hemispec` CLI, `hemispec-gui` entry point, wheel/sdist, and Windows CLI/GUI artifacts. Current `main` adds the synthetic quickstart and model-cache download code. The public documentation targets that source checkout; these additions are not retroactive features of the archived release.

## v0.1.x priorities

1. Publish current functionality under a new version and immutable tag. Verify the resulting wheel, CLI, GUI, and synthetic quickstart independently, and preserve the archived [v0.1.0 verification record](release-verification-v0.1.0.md).
2. Validate inputs before inference: enforce the released-model grid and affine, reject duplicate subject/session keys, and check classifier atlas/features and optional dependencies before expensive work.
3. Isolate outputs by run and make reruns safe: prevent stale subjects from entering summaries and restrict quickstart cleanup to its own generated files.
4. Repair classifier-cache URLs, verify cached model hashes before loading, and publish versioned compatibility/provenance manifests for reusable assets.
5. Add regression coverage for tied-value Spearman correlations, unsymmetrized TRT matrices, and ROI masks that retain valid zero residuals.
6. Propagate GUI cancellation through classifier/TRT stages and improve missing-asset diagnostics.
7. Add an optional study policy requiring hemisphere-classifier validation. Classification remains opt-in until that policy is implemented and tested; TRT still requires repeated scans.

## v0.2 candidates

- Publish `hemispec-toolkit` to PyPI after release metadata, ownership, and upload checks are complete; until then, continue GitHub Release distribution.
- Zenodo DOI or equivalent archived software citation.
- Richer atlas/custom-bundle downloader or resolver beyond the default released model cache.
- Small approved demo dataset, if redistribution is permitted.
- One-click HTML/PDF report generation.
- Release CI that builds and uploads Windows artifacts automatically.
- Stronger classifier/TRT output interpretation docs.
- Manuscript, citation, and data-availability pages once the paper/archive DOI is public.

## Non-goals for tracked source

Do not add unapproved model weights, atlas NIfTI files, real MRI inputs, generated outputs, private paths, or unpublished manuscript-only payloads to the source repository. The approved reusable DGN/classifier bundles under `assets/models/` are the explicit Git-LFS exception; publish any additional assets separately with manifests and checksums.

## Related pages

- [v0.1.0 release verification](release-verification-v0.1.0.md)
- [Release artifacts](../release-artifacts.md)
- [External asset bundles](../reference/asset-bundle.md)
