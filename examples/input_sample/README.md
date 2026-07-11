# Input sample policy

Real subject-level MRI files are not distributed from this directory.

Use the public synthetic example under:

```text
examples/synthetic_quickstart/
```

Local approved inputs may be placed here for private development, but NIfTI files are ignored by git and must not be committed. A valid model input normally ends with `_GM_masked.nii.gz`; see the documentation page `docs/input-preprocessing.md` for the complete grid, value-range, preprocessing, and quality-control contract.
