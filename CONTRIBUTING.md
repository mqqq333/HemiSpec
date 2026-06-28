# Contributing to HemiSpec

HemiSpec is organized as a single software repository: documentation website, Python package, CLI, GUI entry point, examples, tests, and release scripts live together.

## Development setup

```bash
python -m pip install -e .[dev]
python -m pytest
```

Optional runtime extras:

```bash
python -m pip install -e .[model]
python -m pip install -e .[classifier]
```

Documentation preview:

```bash
python -m pip install -r requirements-docs.txt
python -m mkdocs serve
```

## Engineering rules

- Runtime code lives under `src/hemispec/`.
- CLI and GUI layers should stay thin and delegate to the API/workflow modules.
- Public naming is **HemiSpec**, `hemispec`, `hemispec-toolkit`, and `hemispec-gui`.
- ANS and RNS remain metric names, not the package brand.
- Do not commit real subject-level MRI/NIfTI files, trained weights, classifier bundles, private paths, or generated outputs.
- Public examples must be synthetic or explicitly approved for redistribution.
- Large runtime assets belong outside the wheel and should be released with manifests/checksums.

## Validation before commit

```bash
python -m pytest
python -m build --wheel --sdist
python -m hemispec --help
python -m mkdocs build --strict
```

For the public example:

```powershell
powershell -ExecutionPolicy Bypass -File examples\synthetic_quickstart\run_synthetic_quickstart.ps1 -Python python
```
