# HemiSpec Materials TODO

This file tracks the materials still needed before the HemiSpec site should be pushed as a public software homepage.

## P0: Needed before public release

- Manuscript figures: project owner approved adding current manuscript-derived figures to the homepage on 2026-06-28. Still avoid private subject-level data, unpublished raw result tables, and unapproved exact-result claims; do not push/deploy without explicit user approval.
- Decide whether the toolkit source is copied into this repository, linked as a companion repository, or managed as a submodule.
- Add a small, license-safe example dataset or synthetic input/output fixture. **Done:** toolkit now includes a public-safe synthetic quickstart generator and runner.
- Add a model bundle policy: repository, GitHub Releases, Zenodo/OSF, or private request.
- Decide the release artifact split: PyPI `hemispec-toolkit`, CLI `hemispec`, GUI `hemispec-gui`, lightweight compiled app, and model-enabled compiled app.
- Add citation status for the handedness manuscript when a public manuscript/preprint citation is available.
- Decide whether `CLAUDE.md` remains local-only or is converted into a public contributor note.

## P1: Needed for a usable software homepage

- Review whether additional manuscript figures beyond the public-safe study-design overview can be shown after preprint/submission. **Done for current draft:** project owner approved adding manuscript-derived figures to the homepage on 2026-06-28; figures were metadata-stripped and web-optimized before commit.
- Add screenshots of the HemiSpec GUI pages after branding cleanup. **Partial:** added a public-safe schematic GUI preview; replace or supplement with real GUI screenshots before final public launch.
- Add CLI examples for DGN inference, ANS/RNS computation, ROI extraction, TRT validation, and reporting.
- Add Python API examples from the current toolkit implementation.
- Add expected output tables and directory layout.
- Add a model bundle manifest example with weights, config, preprocessing assumptions, and version metadata.
- Add validation results that can be publicly shared.
- Decide whether public quickstart should ship a real `assets/` directory or remain a planned layout until assets are approved.

## P2: Useful polish

- Enable GitHub Pages in repository settings with GitHub Actions as the source after the docs workflow is committed and pushed.
- Add issue templates for bug reports and documentation requests.
- Add a changelog and release notes.
- Keep package, CLI, GUI, and public documentation names strictly aligned to HemiSpec / `hemispec`.
- Add contributor notes for method citations and data-use boundaries.

## Private local sources

Machine-specific source paths are kept in `PRIVATE_NOTES.md`, which is ignored by git. Do not publish those paths in public docs.

## Completed cleanup

- Legacy `src/`, `img/`, and `demo/` files have been removed from the public git index and should remain local/ignored unless deliberately archived elsewhere.


## Materials to request from server or local assets

When moving from the public-safe skeleton to a model-enabled release, request the
following as explicit release bundles, not as ad-hoc paths:

- DGN model bundle: left-to-right and right-to-left checkpoints, architecture/crop
  config, training summary, compatibility version, and SHA256 checksums.
- Classifier bundle: saved joblib pipelines, feature names, mode (`single` or
  `paired_residual`), model card, provenance, and checksums.
- Atlas bundle: Glasser atlas NIfTI and label table, source/license notes,
  checksum, expected environment variables, and compatibility with the toolkit.
- GUI screenshots: public-safe screenshots using synthetic or approved inputs.
- Manuscript assets: final public figure legends and citation text after the
  manuscript/preprint boundary is finalized.


## Visual style guidelines

- Prefer manuscript figures and manually drawn scientific schematics for method
  and result communication.
- AI-generated images may be used for homepage decoration or abstract workflow
  illustrations, but they must be labeled or framed as schematic/illustration,
  never as empirical results.
- If extra workflow/pipeline figures are needed, it is acceptable to learn from
  the visual grammar of Wang et al. 2024, *Patterns* (modular input ? model ?
  metric ? validation flow), but do not directly reuse or trace their figures.
- Keep visual style simple, rigorous, and research-oriented: restrained colors,
  readable labels, minimal shadows, no flashy promotional effects.
- The user has noted that paper2post-style API generation can be used for AI
  illustrations when needed.
