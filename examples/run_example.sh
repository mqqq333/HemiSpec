#!/usr/bin/env bash
set -euo pipefail

hemispec compute \
  --actual-glob "./data/gm/*.nii.gz" \
  --predicted-glob "./data/recon/*_PRED_LR_full.nii.gz" \
  --out-dir "./outputs/ANS_RNS_thr0p15" \
  --gm-thresh 0.15 \
  --save-subject-maps

hemispec specificity \
  --maps-dir "./outputs/ANS_RNS_thr0p15/subject_maps" \
  --out-dir "./outputs/specificity" \
  --session-a run-01 \
  --session-b run-02

