# Roadmap

This page tracks public-facing HemiSpec development after the v0.1.0 first public beta.

## Current status

HemiSpec v0.1.0 was published on 2026-06-29 as a GitHub prerelease: [https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0](https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0). It is research software / public beta, not a mature clinical or commercial product.

The release includes the unified HemiSpec repository, documentation website, `hemispec` CLI, `hemispec-gui` entry point, wheel/sdist, Windows CLI/GUI artifacts, synthetic quickstart, CI/docs gates, and external-asset distribution policy.

## v0.1.x priorities

1. Keep the release downloadable and reproducible: checksum release assets, smoke-test the CLI, and run the synthetic quickstart from the released wheel. Baseline established on 2026-06-29; see [v0.1.0 release verification](release-verification-v0.1.0.md).
2. Make first-run documentation clearer: prominent download links, quickstart path, and asset/model boundaries.
3. Harden asset handling: keep approved DGN/classifier bundles reusable through Git LFS and first-run cache download; keep manifest/checksum/license/provenance templates for atlas and custom/offline bundles.
4. Improve GUI diagnostics: setup status card now shows DGN model, Glasser atlas, classifier bundle, and PyTorch availability as found/missing/download-pending; next steps are checksum display and richer first-run guidance.
5. Improve error messages and logs for missing models, missing atlas files, missing classifier bundles, and missing optional dependencies.

## v0.2 candidates

- Continue PyPI publication of `hemispec-toolkit` alongside GitHub release artifacts.
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
