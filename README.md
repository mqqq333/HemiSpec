# HemiSpec

**HemiSpec: Reconstruction-derived Hemispheric Specificity**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](#)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

HemiSpec is a unified software and documentation project for reconstruction-derived hemispheric specificity analysis. The recommended user path is the PyPI package: it manages the Python runtime dependencies and installs the `hemispec` CLI and `hemispec-gui` entry points in the same environment that carries PyTorch and model-cache access. The repository also contains the MkDocs Material website, public-safe examples, tests, and release scripts.

<p align="center">
  <img src="docs/assets/figures/hemispec-study-design.png" alt="HemiSpec study design overview" width="100%">
</p>

## Recommended PyPI install / Download v0.1.0

HemiSpec v0.1.0 is available as a first public beta / research-software release. PyPI is the primary install path because model-enabled workflows need a real Python/PyTorch environment; the CLI and GUI are entry points installed by that package rather than separate primary products.

Install the full model/GUI-capable package from PyPI:

```bash
python -m pip install "hemispec-toolkit[gui,model,classifier]"
hemispec --help
```

GitHub Release artifacts remain available for archived, offline, or Windows-folder fallback installs:

- GitHub Release: https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0
- Windows CLI: `HemiSpec-CLI-v0.1.0-win64.exe`
- Windows GUI: `HemiSpec-GUI-v0.1.0-win64.zip`
- Python artifacts: `hemispec_toolkit-0.1.0-py3-none-any.whl` and `hemispec_toolkit-0.1.0.tar.gz`

The source repository carries reusable DGN generator checkpoints and hemisphere-classifier bundles under `assets/models/` via Git LFS, so users can run model-enabled workflows without retraining. Wheels and lightweight desktop builds do not embed the 300 MB+ weights, but the PyPI-installed CLI/GUI/API can auto-download the released model assets into a per-user cache on first model run. The normal path is: input preprocessed GM maps -> run HemiSpec -> get ANS/RNS maps. See [Data and models](docs/data-and-models.md) before publishing or redistributing additional assets.

## Method boundary

The ANS/RNS metric framework and the original cross-hemispheric DGN approach originate from Wang et al. 2024, *Patterns*, "Using a deep generation network reveals neuroanatomical specificity in hemispheres". HemiSpec builds on that framework and organizes reusable software tooling plus behavioral-phenotype downstream-analysis workflows around it.

ANS and RNS remain metric names. The public package, CLI, GUI, and project identity are **HemiSpec**.

## Repository layout

```text
src/hemispec/              Python package, public API, CLI, GUI, workflows
docs/                      MkDocs Material documentation website
tests/                     pytest regression tests with synthetic fixtures
examples/                  public-safe examples and IO contracts
scripts/                   release/local launcher helpers; research utilities are isolated in scripts/research
assets/                    reusable model bundles plus local atlas/data placement docs
.github/workflows/         CI and GitHub Pages workflows
```

Reusable DGN checkpoints and classifier bundles are tracked with Git LFS. Real subject-level NIfTI files and generated outputs remain excluded.

## Install for development

For normal use, install the released package from PyPI as shown above. For local development from a source checkout:

```bash
python -m pip install -e .[dev]
python -m pytest
```

Model-enabled source-checkout extras:

```bash
python -m pip install -e .[gui,model,classifier]
hemispec models --install --with-classifier  # optional pre-download; otherwise first model run downloads
```

## PyPI-installed CLI

```bash
hemispec --help
python -m hemispec --help
```

## Model-enabled GUI

For normal use, launch the GUI from the same PyPI/conda environment that contains PyTorch and HemiSpec. Clone with Git LFS only when you want a source checkout with repository model files:

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e .[gui,model,classifier]
python scripts/hemispec_gui_entry.py
```

The GUI setup card should report the DGN model and classifier bundle as found after Git-LFS checkout or PyPI cache download. In a PyPI install, the first model run downloads the released model assets to the user cache if they are not already present. Provide preprocessed `*_GM_masked.nii.gz` inputs and choose an output workspace.

## Public-safe quickstart

```bash
python -m pip install hemispec-toolkit
hemispec quickstart --out-dir hemispec_quickstart
```

The built-in synthetic example creates toy NIfTI maps and validates the public file/command contract without private MRI data, model weights, or a source checkout. Source-tree wrapper scripts remain under `examples/synthetic_quickstart/` for development.

## Documentation site

```bash
python -m pip install -r requirements-docs.txt
python -m mkdocs serve
```

Build strictly before publishing:

```bash
python -m mkdocs build --strict
```

## Citation

If you use the reconstruction-derived ANS/RNS framework, cite the original Patterns paper:

Wang, G. et al. (2024). Using a deep generation network reveals neuroanatomical specificity in hemispheres. *Patterns*, 5, 100930. https://doi.org/10.1016/j.patter.2024.100930

A separate HemiSpec handedness manuscript/software citation will be added when the manuscript, archive DOI, or release record is public.

## License

MIT. See [LICENSE](LICENSE).
