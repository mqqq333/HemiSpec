#!/usr/bin/env bash
set -euo pipefail

PYTHON="${PYTHON:-python}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKDIR="${1:-"$SCRIPT_DIR/workdir"}"

"$PYTHON" "$SCRIPT_DIR/make_synthetic_nifti.py" --out-dir "$WORKDIR"
"$PYTHON" -m hemispec compute \
  --actual-glob "$WORKDIR/actual/*.nii.gz" \
  --predicted-glob "$WORKDIR/recon/*_PRED_LR_full.nii.gz" \
  --out-dir "$WORKDIR/outputs/compute" \
  --save-subject-maps \
  --roi-atlas "$WORKDIR/atlas/toy_atlas.nii.gz" \
  --roi-label-table "$WORKDIR/atlas/toy_labels.csv" \
  --roi-out-csv "$WORKDIR/outputs/compute/toy_roi_summary.csv"

echo "[HemiSpec synthetic] Done: $WORKDIR/outputs/compute"
