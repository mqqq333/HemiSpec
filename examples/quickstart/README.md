# Quickstart example

The public website keeps only a lightweight pointer here. The runnable synthetic
demo lives in the HemiSpec Toolkit repository under:

```text
examples/synthetic_quickstart/
```

It generates public-safe toy NIfTI maps and mock reconstruction outputs, then
runs:

```bash
hemispec compute \
  --actual-glob "workdir/actual/*.nii.gz" \
  --predicted-glob "workdir/recon/*_PRED_LR_full.nii.gz" \
  --out-dir "workdir/outputs/compute" \
  --save-subject-maps \
  --roi-atlas "workdir/atlas/toy_atlas.nii.gz" \
  --roi-label-table "workdir/atlas/toy_labels.csv" \
  --roi-out-csv "workdir/outputs/compute/toy_roi_summary.csv"
```

Do not add real subject data here unless redistribution has been approved.
