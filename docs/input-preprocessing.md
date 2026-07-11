# Input and preprocessing

This page defines how a T1-weighted structural MRI becomes an input for the released HemiSpec DGN models.

## Two different inputs must not be confused

| Workflow boundary | Accepted input |
| --- | --- |
| `process_single_subject.sh` | One raw or minimally processed T1-weighted MRI in NIfTI format, normally `*_T1w.nii.gz` |
| HemiSpec DGN workflow | One preprocessed, MNI-space, masked gray-matter map per subject, normally `*_GM_masked.nii.gz` |

!!! danger "Do not pass raw T1 images to `hemispec workflow`"
    Raw T1 intensities, skull-on T1 images, native-space tissue maps, and maps on a different template grid are not valid inputs for the released DGN checkpoints.

## Scientific preprocessing contract

Wang et al. (2024) describe the original method-level preprocessing as follows: T1-weighted images are segmented into tissue classes; GM density maps are normalized to MNI space at `1.5 × 1.5 × 1.5 mm³`, scaled to `0–1`, and thresholded with a GM probability threshold of `0.15` before hemisphere splitting and cropping.

The project-level `process_single_subject.sh` script operationalizes this input preparation with FSL BET, FAST, FLIRT, and `fslmaths`. The script is a local implementation; the original scientific framework and preprocessing requirements should still be attributed to Wang et al. (2024).

## Canonical study script

The script identified in the study workflow is at the repository root:

```text
process_single_subject.sh
```

It is Bash-based and requires a working FSL installation. On Windows, run preprocessing inside Linux, WSL, an HPC environment, or another environment where FSL is supported. The generated NIfTI file can then be used by HemiSpec on Windows or Linux.

The Python package also contains an alternative hardened variant:

```text
src/hemispec/resources/preprocess/process_single_subject_GM_v2_reorient.sh
```

That variant adds explicit reorientation and estimates the T1-to-MNI affine from the brain-extracted T1 before applying the transform to the GM partial-volume map. **Do not mix preprocessing variants within one cohort.** Record the exact script filename and revision in the study protocol.

## Prerequisites

Before running `process_single_subject.sh`:

1. Install and validate FSL.
2. Set `FSLDIR` and source the FSL configuration.
3. Confirm that this reference exists:

```text
${FSLDIR}/data/standard/MNI152_T1_1.5mm_brain.nii.gz
```

A typical shell setup is:

```bash
export FSLDIR=/path/to/fsl
source "${FSLDIR}/etc/fslconf/fsl.sh"
export PATH="${FSLDIR}/bin:${PATH}"
```

## Run one subject

The script takes exactly two positional arguments:

```text
process_single_subject.sh INPUT_T1 OUTPUT_PREFIX
```

Example:

```bash
bash process_single_subject.sh \
  raw/sub-001_T1w.nii.gz \
  derivatives/sub-001
```

Expected final DGN input:

```text
derivatives/sub-001_GM_masked.nii.gz
```

The processing log is:

```text
derivatives/sub-001_debug.log
```

The current study script removes its intermediate BET, FAST, FLIRT, and mask products after successful processing. If intermediate images are required for a formal QC record, run a retained-copy variant or temporarily disable cleanup in a version-controlled study copy; document that change.

## What `process_single_subject.sh` does

| Step | FSL command | Purpose | Main output |
| --- | --- | --- | --- |
| 1 | `bet -f 0.4 -B` | Brain extraction and bias/neck cleanup | `<prefix>_T1_bet.nii.gz` |
| 2 | `fast -R 0.3 -H 0.1` | Segment the brain into tissue probability maps | `<prefix>_seg_pve_1.nii.gz` (GM PVE) |
| 3 | `flirt` | Affine-register the GM partial-volume map to the FSL MNI152 1.5 mm brain | `<prefix>_GM_linear_MNI.nii.gz` |
| 4a | `fslmaths -thr 0.15 -bin` | Create a GM probability mask | `<prefix>_GM_mask.nii.gz` |
| 4b | `fslmaths -mul` | Apply the mask to the MNI-space GM probability map | `<prefix>_GM_masked.nii.gz` |
| 5 | `rm` | Remove intermediate files after the final output is written | final GM map + debug log retained |

## DGN-ready output contract

The released HemiSpec checkpoints and public examples use the following contract:

| Property | Expected value |
| --- | --- |
| Dimensionality | One 3D volume per subject |
| Data type | Numeric NIfTI data; repository examples are `float32` |
| Value range | Finite GM probability/density values, normally `0–1` |
| Template | FSL MNI152 T1 1.5 mm brain |
| Grid | `121 × 145 × 121` voxels |
| Voxel size | `1.5 × 1.5 × 1.5 mm³` |
| Affine | Must match the FSL reference; compare the complete affine, not only dimensions |
| Filename | Stable subject identifier followed by `_GM_masked.nii.gz` |

HemiSpec identifies subjects by removing configured filename suffixes. Every file matched by one workflow glob should therefore have a unique and stable prefix.

## Quality control before DGN inference

Do not rely on filename matching alone. For every cohort, inspect at least the following:

1. **Brain extraction:** no large remaining skull/neck signal and no major cortical loss.
2. **Tissue segmentation:** the GM partial-volume map follows cortical and subcortical GM rather than WM/CSF.
3. **MNI alignment:** the transformed GM map overlaps the MNI152 1.5 mm reference without gross translation, rotation, scaling, or left-right errors.
4. **Grid consistency:** all subjects have the same shape, voxel size, orientation, and affine as the reference and as each other.
5. **Value range:** values are finite and normally within `0–1`; background is zero.
6. **Mask quality:** the `0.15` threshold removes low-probability edge noise without eliminating large GM regions.
7. **Visual cohort review:** failed BET, FAST, or FLIRT cases are excluded or reprocessed before DGN inference.

Useful FSL checks:

```bash
fslhd derivatives/sub-001_GM_masked.nii.gz
fslstats derivatives/sub-001_GM_masked.nii.gz -R -V
fsleyes \
  "${FSLDIR}/data/standard/MNI152_T1_1.5mm_brain.nii.gz" \
  derivatives/sub-001_GM_masked.nii.gz
```

A small Python check:

```python
from pathlib import Path
import nibabel as nib
import numpy as np

path = Path("derivatives/sub-001_GM_masked.nii.gz")
img = nib.load(path)
data = img.get_fdata(dtype=np.float32)

assert img.shape == (121, 145, 121)
assert np.allclose(img.header.get_zooms()[:3], (1.5, 1.5, 1.5))
assert np.isfinite(data).all()
assert data.min() >= 0
assert data.max() <= 1.0 + 1e-5
```

## Batch example

```bash
mkdir -p derivatives
for t1 in raw/sub-*/anat/*_T1w.nii.gz; do
  subject=$(basename "$t1" _T1w.nii.gz)
  bash process_single_subject.sh "$t1" "derivatives/$subject"
done
```

After quality control, run HemiSpec on the resulting files:

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_workflow
```

## Thresholds used at different stages

- `process_single_subject.sh` creates the final GM mask at probability `0.15`.
- DGN inference contains an additional low-value input cleanup at `0.05`; a correctly produced `0.15`-masked input is already stricter than this cleanup.
- ANS/RNS computation uses a default valid-GM threshold of `0.15`.

Keep these thresholds documented in a study protocol. Changing them alters the input support or metric support and should be treated as a methodological change.

## Citations for preprocessing

When reporting this workflow, cite both the original ANS/RNS framework and the FSL methods used by the implementation. Full references are listed on the [Citation](citation.md) page.
