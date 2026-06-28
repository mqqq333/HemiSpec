# Changelog

All notable changes to HemiSpec will be recorded here.

## [Unreleased]

### Added

- Unified HemiSpec repository layout combining documentation website and toolkit package.
- `src/hemispec` package, `hemispec` CLI, and `hemispec-gui` entry point.
- MkDocs Material documentation site with left-side navigation.
- Public-safe synthetic quickstart and release/build scripts.
- Compact customtkinter standard-workflow GUI for ANS/RNS generation, optional ROI export, classifier validation, and TRT reliability.
- v0.1.0 local release artifacts for Windows CLI/GUI, wheel, sdist, checksums, and external asset policy.

### Changed

- Public identity aligned to HemiSpec while keeping ANS/RNS as metric names.
- Documentation aligned with the compact GUI workflow, MkDocs Pages deployment, and release/data-model guidance.

### Fixed

- TRT boxplot generation now supports Matplotlib versions that use `tick_labels` instead of `labels` (Matplotlib >= 3.9).

### Removed

- Legacy prototype homepage/code assets and private payloads from the public tracked surface.
