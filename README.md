# HemiSpec

**HemiSpec: Reconstruction-derived Hemispheric Specificity**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](#)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

HemiSpec is a unified software and documentation project for reconstruction-derived hemispheric specificity analysis. It combines a MkDocs Material project website, Python package, `hemispec` CLI, `hemispec-gui` entry point, public-safe examples, tests, and release scripts in one repository.

<p align="center">
  <img src="docs/assets/figures/hemispec-study-design.png" alt="HemiSpec study design overview" width="100%">
</p>

## Download v0.1.0

HemiSpec v0.1.0 is available as a first public beta / research-software release:

- GitHub Release: https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0
- Windows CLI: `HemiSpec-CLI-v0.1.0-win64.exe`
- Windows GUI: `HemiSpec-GUI-v0.1.0-win64.zip`
- Python artifacts: `hemispec_toolkit-0.1.0-py3-none-any.whl` and `hemispec_toolkit-0.1.0.tar.gz`

The source repository carries reusable DGN generator checkpoints and hemisphere-classifier bundles under `assets/models/` via Git LFS, so users can run model-enabled workflows without retraining. Wheels and lightweight desktop builds do not embed the 300 MB+ weights, but the CLI/GUI/API can auto-download the released model assets into a per-user cache on first model run. The normal path is: input preprocessed GM maps -> run HemiSpec -> get ANS/RNS maps. See [Data and models](docs/data-and-models.md) before publishing or redistributing additional assets.

## Method boundary

The ANS/RNS metric framework and the original cross-hemispheric DGN approach originate from Wang et al. 2024, *Patterns*, "Using a deep generation network reveals neuroanatomical specificity in hemispheres". HemiSpec builds on that framework and organizes the current handedness-focused workflow and reusable software tooling around it.

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

```bash
python -m pip install -e .[dev]
python -m pytest
```

Model-enabled runtime extras:

```bash
python -m pip install -e .[gui,model,classifier]
hemispec models --install --with-classifier  # optional pre-download; otherwise first model run downloads
```

## CLI

```bash
hemispec --help
python -m hemispec --help
```

## Model-enabled GUI from source

Clone with Git LFS so model bundles are downloaded:

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e .[gui,model,classifier]
python scripts/hemispec_gui_entry.py
```

The GUI setup card should report the DGN model and classifier bundle as found in a Git-LFS checkout. In a wheel/PyPI install, the first model run downloads the released model assets to the user cache if they are not already present. Provide preprocessed `*_GM_masked.nii.gz` inputs and choose an output workspace.

## Public-safe quickstart

```powershell
powershell -ExecutionPolicy Bypass -File examples\synthetic_quickstart\run_synthetic_quickstart.ps1 -Python python
```

On macOS/Linux:

```bash
bash examples/synthetic_quickstart/run_synthetic_quickstart.sh
```

The synthetic example creates toy NIfTI maps and validates the public file/command contract without private MRI data or model weights.

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
