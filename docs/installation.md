# Installation

HemiSpec has four installation/release layers: documentation site, Python package, CLI/GUI entry points, and compiled desktop folders.

## Documentation site

Install the MkDocs dependencies from the repository root:

```bash
python -m pip install -r requirements-docs.txt
mkdocs serve
```

MkDocs prints a local preview URL after startup.

## Toolkit / PyPI package

During migration, use your local toolkit checkout. The public package target is the PyPI distribution `hemispec-toolkit` with import path `hemispec`:

```bash
cd <local-toolkit-checkout>
python -m pip install -e .
hemispec --help
```

Install the optional GUI dependency when you want the desktop launcher:

```bash
python -m pip install -e .[gui]
hemispec-gui
```

Install optional runtime extras only when needed:

```bash
python -m pip install -e .[model]       # PyTorch DGN inference runtime
python -m pip install -e .[classifier]  # saved sklearn/joblib classifier validation
python -m pip install -e .[dev,gui]     # tests, build tools, GUI development
```

Public documentation should call the software **HemiSpec Toolkit**. Use `hemispec` and `hemispec-gui` consistently for the public CLI and GUI.

## Neuroimaging prerequisites

The preprocessing workflow depends on FSL tools such as BET, FAST, FLIRT, and `fslmaths`. Inputs to the toolkit are expected to be gray-matter maps in a consistent MNI-space grid, thresholded and masked according to the workflow assumptions.

## GUI / compiled app

The current GUI is a compact standard-workflow launcher. It exposes only user decisions needed for normal ANS/RNS generation: GM input glob, output workspace, optional ROI atlas/label table, optional classifier validation, optional TRT reliability, run controls, logs, and an equivalent CLI command.

The compiled Windows GUI is an onedir folder distribution:

```text
dist/hemispec_gui/hemispec_gui.exe
```

Keep the whole `dist/hemispec_gui/` folder together; do not move only the `.exe`.

## Optional model runtime

DGN inference requires a PyTorch environment and trained DGN model bundles. Model weights, atlas payloads, classifier bundles, and real subject-level MRI derivatives are not stored in the source repository. See [Data and models](data-and-models.md) for the release policy and local directory conventions.
