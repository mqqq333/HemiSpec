# HemiSpec

**HemiSpec: Reconstruction-derived Hemispheric Specificity**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](#)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-MkDocs-indigo)](https://mqqq333.github.io/HemiSpec/)

HemiSpec is a research-software toolkit for generating reconstruction-derived hemispheric maps from T1-weighted structural MRI. It packages a reproducible path from **preprocessed gray-matter (GM) maps** to bilateral **ANS/RNS maps**, optional ROI tables, and validation outputs.

> **Scientific attribution.** The cross-hemispheric deep generation network (DGN) framework and the ANS/RNS metrics were introduced by Wang et al. (2024). HemiSpec is the software, documentation, packaging, and downstream-workflow layer built around that published method; it does not claim authorship of the original DGN or ANS/RNS definitions.

<p align="center">
  <img src="docs/assets/figures/hemispec-study-design.png" alt="HemiSpec study design overview" width="100%">
</p>

## From T1 MRI to HemiSpec outputs

```text
T1-weighted MRI (.nii.gz)
        |
        |  FSL preprocessing: BET -> FAST -> FLIRT -> GM mask
        v
MNI152 1.5 mm gray-matter map (*_GM_masked.nii.gz)
        |
        |  bilateral DGN reconstruction + ANS/RNS computation
        v
ANS.L / ANS.R / RNS.L / RNS.R maps
        |
        +--> optional ROI tables
        +--> optional hemisphere-classifier and TRT validation
```

**Raw T1 images are not direct DGN inputs.** Each T1 image must first be converted into the GM input expected by the released models.

### DGN input contract

| Item | Required value |
| --- | --- |
| File format | NIfTI, normally `.nii.gz` |
| Filename | One subject per file; recommended suffix `*_GM_masked.nii.gz` |
| Image content | Gray-matter probability/density values, finite and normally scaled to `0–1` |
| Spatial reference | FSL `MNI152_T1_1.5mm_brain.nii.gz` grid |
| Expected released-model grid | `121 × 145 × 121` voxels at `1.5 mm` isotropic resolution |
| Background handling | GM probability threshold `0.15`, then mask applied to the GM map |
| Quality control | Inspect skull stripping, tissue segmentation, registration, value range, shape, voxel size, and affine |

The study preprocessing script is:

```text
process_single_subject.sh
```

It accepts a T1 NIfTI and an output prefix. The Python package also contains a documented reorientation-enhanced variant under `src/hemispec/resources/preprocess/`; do not mix script variants within one cohort:

```bash
bash process_single_subject.sh \
  raw/sub-001_T1w.nii.gz \
  derivatives/sub-001
```

The DGN-ready output is:

```text
derivatives/sub-001_GM_masked.nii.gz
```

See the detailed [Input and preprocessing guide](https://mqqq333.github.io/HemiSpec/input-preprocessing/) before running real MRI data.

## Install

HemiSpec v0.1.0 is a public beta. The recommended installation is the PyPI package in the same Python/conda environment that provides PyTorch:

```bash
python -m pip install "hemispec-toolkit[gui,model,classifier]"
hemispec models --install --with-classifier  # optional pre-download
hemispec --help
```

For a source checkout with the released model files tracked through Git LFS:

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e .[gui,model,classifier]
```

## Run the standard bilateral workflow

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_workflow
```

Or launch the GUI from the same environment:

```bash
hemispec-gui
```

Current primary outputs are written under:

```text
outputs/hemispec_workflow/
├── voxel_maps/          # <subject>_ANS.L/R and <subject>_RNS.L/R
├── tables/              # subject summary and optional ROI tables
└── validation/          # optional classifier/TRT outputs
```

Hemisphere-classifier validation is currently an **optional downstream validation step** and requires ROI feature export. A future software update may add a study-level policy that marks this validation as mandatory; this documentation update does not change current software behavior.

## Public-safe smoke test

The synthetic quickstart verifies installation and file contracts without real MRI data or model weights:

```bash
python -m pip install hemispec-toolkit
hemispec quickstart --out-dir hemispec_quickstart
```

Synthetic outputs are not anatomical results and must not be used for scientific interpretation.

## Method and citation boundary

Use the original paper when citing the cross-hemispheric DGN method or ANS/RNS metrics:

> Wang, G., Jiang, N., Ma, Y., Suo, D., Liu, T., Funahashi, S., & Yan, T. (2024). Using a deep generation network reveals neuroanatomical specificity in hemispheres. *Patterns, 5*(4), 100930. https://doi.org/10.1016/j.patter.2024.100930

In the original paper:

- **ANS** means **absolute neuroanatomical specificity**.
- **RNS** means **relative neuroanatomical specialization**.

HemiSpec-specific software, release, and downstream-study citations should be added separately when their public archival records are available. See the full [citation guidance](https://mqqq333.github.io/HemiSpec/citation/).

## Repository layout

```text
src/hemispec/              Python package, public API, CLI, GUI, workflows
process_single_subject.sh  Study FSL T1-to-GM preprocessing script
src/hemispec/resources/    Packaged reorientation-enhanced preprocessing variant
assets/                    DGN/classifier bundles and atlas assets
examples/                  Public-safe examples and input/output contracts
tests/                     pytest regression tests
docs/                      Bilingual MkDocs documentation
scripts/                   Build, release, and local launcher helpers
```

Real subject-level MRI data and generated study outputs are not part of the public software distribution.

## Development and documentation

```bash
python -m pip install -e .[dev,gui]
python -m pytest
python -m ruff check src tests
python -m pip install -r requirements-docs.txt
python -m mkdocs build --strict
```

## Release artifacts

GitHub Release v0.1.0 contains archived/fallback Windows and Python artifacts:

- https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0
- `HemiSpec-CLI-v0.1.0-win64.exe`
- `HemiSpec-GUI-v0.1.0-win64.zip`
- `hemispec_toolkit-0.1.0-py3-none-any.whl`
- `hemispec_toolkit-0.1.0.tar.gz`

## License

MIT. See [LICENSE](LICENSE).
