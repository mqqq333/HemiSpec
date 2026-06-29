# Installation

HemiSpec has four installation/release layers: documentation site, Python package, CLI/GUI entry points, and compiled desktop folders.

## Documentation site

Install the MkDocs dependencies from the repository root:

```bash
python -m pip install -r requirements-docs.txt
mkdocs serve
```

MkDocs prints a local preview URL after startup.

## Model-enabled install

For a PyPI/wheel install, install the runtime extras and optionally pre-download the released model assets into the user cache:

```bash
python -m pip install "hemispec-toolkit[gui,model,classifier]"
hemispec models --install --with-classifier
hemispec-gui
```

If you skip the pre-download command, the first model-enabled CLI/GUI/API run downloads the released DGN checkpoints automatically. Classifier bundles auto-download when classifier validation is enabled.

Use a Git-LFS source checkout when you want the repository copy of the bundled DGN and classifier models:

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e .[gui,model,classifier]
python scripts/hemispec_gui_entry.py
```

On Windows, launch the same commands from the conda environment that has PyTorch installed if you need GPU/CUDA support.

## Toolkit / release package

HemiSpec v0.1.0 is available from the GitHub Release page:

```text
https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0
```

Download the wheel for a lightweight Python install:

```bash
python -m pip install hemispec_toolkit-0.1.0-py3-none-any.whl
hemispec --help
```

The PyPI distribution name is `hemispec-toolkit`; the import path and CLI command are `hemispec`. During development, use your local toolkit checkout:

```bash
cd <local-toolkit-checkout>
python -m pip install -e .[gui,model,classifier]
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

## Model runtime

DGN inference requires PyTorch in the environment that starts the CLI or GUI. HemiSpec discovers models from explicit paths, environment variables, a Git-LFS checkout under `assets/models/`, or the per-user model cache. Wheel/PyPI and lightweight EXE builds do not embed PyTorch or the 300 MB+ checkpoints; they use the released GitHub assets through first-run cache download. See [Data and models](data-and-models.md).
