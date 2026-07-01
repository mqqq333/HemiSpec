# Installation

HemiSpec is PyPI-first. Install the Python package into the environment that will run PyTorch and access the model cache; the `hemispec` CLI and `hemispec-gui` launcher are entry points created by that package. Compiled desktop folders and GitHub Release wheels are fallback or archival artifacts.

## Recommended: model-enabled PyPI environment

Install the released package from PyPI with the runtime extras in the Python/conda environment you plan to use for inference. Then optionally pre-download the released model assets into the user cache:

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

On Windows, run HemiSpec from the conda or virtual environment that has the desired PyTorch build. For GPU/CUDA work, configure PyTorch in that environment first, then install or run HemiSpec there.

## Base package, fallbacks, and development installs

The PyPI distribution name is `hemispec-toolkit`; the import path and CLI command are `hemispec`:

```bash
python -m pip install hemispec-toolkit
hemispec --help
hemispec quickstart --out-dir hemispec_quickstart
```

GitHub Release artifacts remain available as a fallback for offline, archived, or Windows-folder installs:

```text
https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0
```

For a local wheel downloaded from GitHub Releases:

```bash
python -m pip install hemispec_toolkit-0.1.0-py3-none-any.whl
hemispec --help
```

During development, use your local toolkit checkout:

```bash
cd <local-toolkit-checkout>
python -m pip install -e .[gui,model,classifier]
hemispec --help
```

Install optional runtime extras only when needed:

```bash
python -m pip install "hemispec-toolkit[gui]"         # desktop launcher
python -m pip install "hemispec-toolkit[model]"       # PyTorch DGN inference runtime
python -m pip install "hemispec-toolkit[classifier]"  # saved sklearn/joblib classifier validation
```

For source-checkout development extras:

```bash
python -m pip install -e .[dev,gui]
```

Public documentation should call the software **HemiSpec Toolkit**. Use `hemispec` and `hemispec-gui` consistently for the public CLI and GUI.

## Neuroimaging prerequisites

The preprocessing workflow depends on FSL tools such as BET, FAST, FLIRT, and `fslmaths`. Inputs to the toolkit are expected to be gray-matter maps in a consistent MNI-space grid, thresholded and masked according to the workflow assumptions.

## GUI / compiled-app fallback

The recommended GUI path is `hemispec-gui` from the PyPI-installed environment. The current GUI is a compact standard-workflow launcher. It exposes only user decisions needed for normal ANS/RNS generation: GM input glob, output workspace, optional ROI atlas/label table, optional classifier validation, optional TRT reliability, run controls, logs, and an equivalent CLI command.

The compiled Windows GUI is an onedir folder distribution for fallback/demo use when a managed Python environment is not practical:

```text
dist/hemispec_gui/hemispec_gui.exe
```

Keep the whole `dist/hemispec_gui/` folder together; do not move only the `.exe`.

## Model runtime

DGN inference requires PyTorch in the environment that starts the CLI or GUI, which is why the PyPI/conda environment is the primary distribution path. HemiSpec discovers models from explicit paths, environment variables, a Git-LFS checkout under `assets/models/`, or the per-user model cache. Wheel/PyPI and lightweight EXE builds do not embed PyTorch or the 300 MB+ checkpoints; they use the released GitHub assets through first-run cache download. See [Data and models](data-and-models.md).
