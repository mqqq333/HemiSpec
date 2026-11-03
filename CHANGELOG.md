# Changelog

All notable changes to HemiSpec will be recorded here.

## [Unreleased]

## [0.2.0] - 2026-11-04

### Added

- Co-branded HemiSpec mark, wordmark, 256 px RGBA GUI icon, and multi-size Windows ICO adapted from the 阿瞒的脑洞 / A MAN'S BRAINHOLE circuit-brain head mark.
- Full-width bilingual documentation landing page with hero, four-step workflow, metric formulas, input boundary, method figure, path cards, citation boundary, and scope.
- Four GUI color themes (Cool Teal default, Cool Cyan, Ink Night, Graphite Bronze) with a theme switcher in the header.
- Per-theme HemiSpec header logos for the GUI.

### Changed

- Windows GUI redesigned as a two-pane workbench with a wider analysis pane, Chinese/English UI toggle, queue-based main-thread log polling, stage/progress display, custom high-DPI switches, and pre-run input/output checks.
- Documentation site restyled, with updated installation, CLI, Python API, model-bundle, and project-structure pages.
- ROI mean summaries are computed in a single `bincount` pass, speeding up ROI export.

### Fixed

- GUI worker output now reaches Tk through a queue instead of cross-thread widget calls.
- GUI reports cooperative stop and retained/removed intermediate outputs accurately.
- GUI window sizing now fits the detected work area at high DPI, and Chinese mode translates runtime status, guidance, and mode labels.

## [0.1.0] - 2026-06-28

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
