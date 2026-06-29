# Developer Guide

This guide describes the engineering layout for HemiSpec Toolkit.

## Repository responsibilities

HemiSpec Toolkit has four separable layers:

1. **Library package** (`src/hemispec/`) — importable Python modules and the public API.
2. **Interfaces** (`hemispec` CLI and `hemispec-gui`) — thin entry points over the library package.
3. **Examples and tests** (`examples/`, `tests/`) — synthetic or approved public fixtures plus automated regression checks.
4. **Assets and release bundles** (`assets/`, `dist/`) - approved reusable model bundles, local-only atlases, and compiled outputs.

The approved reusable DGN/classifier bundles live under `assets/models/` with Git LFS. Other large runtime assets should be documented by manifests and released separately unless explicitly approved.

## Local setup

```bash
python -m pip install -e .[dev]
python -m pytest
```

Install optional extras only for the workflow you need:

```bash
python -m pip install -e .[model]
python -m pip install -e .[classifier]
```

## Common checks

```bash
python -m pytest
python -m build --wheel
python -m hemispec --help
hemispec --help
```

The synthetic quickstart should work without any private data:

```powershell
powershell -ExecutionPolicy Bypass -File examples\synthetic_quickstart\run_synthetic_quickstart.ps1 -Python python
```

## Source layout convention

- `api.py` exposes the stable programmatic surface.
- `cli.py` parses commands and delegates to the API/workflow modules.
- `gui.py` is the desktop interface layer; shared computation should not be duplicated there.
- `compute.py`, `similarity.py`, `roi.py`, `reports.py`, and `plots.py` hold focused analysis utilities.
- `workflow.py` coordinates multi-step bilateral workflows.
- `dgn_inference.py` and `dgn_model.py` handle trained DGN inference.
- `hemisphere_classifier.py` handles classifier validation utilities.
- `paths.py` centralizes local asset discovery.
- `resources/` contains small packaged helper scripts only.

If a module grows too large, split by responsibility rather than by call site. For example, GUI-specific widgets can later move into `hemispec/gui_app/`, while CLI subcommands can later move into `hemispec/commands/`.

## Data and asset policy

Do not commit real subject-level MRI/NIfTI files, generated outputs, or unapproved model/atlas payloads. The approved HemiSpec DGN/classifier bundles under `assets/models/` are the explicit exception and must stay tracked through Git LFS. For other assets, commit only:

- README files describing expected placement.
- manifest templates with checksums and provenance fields.
- synthetic fixtures that are safe to redistribute.

## Release policy

The PyPI wheel should stay lightweight and should include package code plus small package-owned resources. Released model weights are resolved from Git LFS or the first-run user cache, not embedded in the wheel. Compiled app folders may be produced under `dist/`, but additional release assets need explicit approval before public upload.
