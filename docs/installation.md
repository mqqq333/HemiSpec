# Installation

HemiSpec has four installation/release layers: the documentation site, the Python/PyPI package, the CLI/GUI entry points, and the compiled desktop app.

## Documentation site

Install the MkDocs dependencies from the repository root:

```bash
python -m pip install -r requirements-docs.txt
mkdocs serve
```

MkDocs prints a local preview URL after startup.

## Toolkit / PyPI package

During migration, use your local toolkit checkout. The final package target is the PyPI distribution `hemispec-toolkit` with import path `hemispec`:

```bash
cd <local-toolkit-checkout>
python -m pip install -e .
hemispec --help
hemispec-gui
```

Public documentation should call the software **HemiSpec Toolkit**. Use `hemispec` and `hemispec-gui` consistently for the public CLI and GUI.

## Neuroimaging prerequisites

The preprocessing workflow depends on FSL tools such as BET, FAST, FLIRT, and `fslmaths`. Inputs to the toolkit are expected to be gray-matter maps in a consistent MNI-space grid, thresholded and masked according to the workflow assumptions.

## Compiled app and optional model runtime

The final user-facing desktop release should be a compiled folder distribution built from the same `hemispec` API. A lightweight GUI app can omit PyTorch/model weights; a model-enabled app should include or explicitly colocate approved DGN/model/atlas asset bundles.

## Optional model runtime

DGN inference requires a PyTorch environment and trained model bundles. Model weights are not yet part of this public homepage repository. See [Data and models](data-and-models.md) for the release policy.