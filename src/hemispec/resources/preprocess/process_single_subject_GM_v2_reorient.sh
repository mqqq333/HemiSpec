#!/bin/bash
# GM v2: reorient first; register T1 brain to MNI; apply that affine to native GM PVE.
# Usage: process_single_subject_GM_v2_reorient.sh input_T1.nii.gz output_prefix
set -euo pipefail

if [ $# -ne 2 ]; then
  echo "Usage: $0 input_T1.nii.gz output_prefix" >&2
  exit 1
fi

input=$1
prefix=$2
outdir=$(dirname "$prefix")
mkdir -p "$outdir"
log="${prefix}_debug_GM_v2.log"

: "${FSLDIR:?Set FSLDIR to your FSL installation root before running this script}"
source "${FSLDIR}/etc/fslconf/fsl.sh"
export PATH="${FSLDIR}/bin:${PATH}"
export FSLOUTPUTTYPE=NIFTI_GZ
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-6}
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=${SLURM_CPUS_PER_TASK:-6}

ref_brain="${FSLDIR}/data/standard/MNI152_T1_1.5mm_brain.nii.gz"
if [ ! -f "$ref_brain" ]; then
  echo "Missing ref: $ref_brain" >&2
  exit 2
fi

run_step() {
  echo "--- $1 | $(date) ---" | tee -a "$log"
  shift
  "$@" >> "$log" 2>&1
}

{
  echo "========== GM v2 start =========="
  echo "start: $(date)"
  echo "host: $(hostname)"
  echo "input: $input"
  echo "prefix: $prefix"
  echo "FSLDIR: $FSLDIR"
  echo "ref_brain: $ref_brain"
  echo "KEEP_INTERMEDIATES: ${KEEP_INTERMEDIATES:-0}"
} > "$log" 2>&1

reor="${prefix}_T1_reorient.nii.gz"
run_step "Step 0 fslreorient2std" fslreorient2std "$input" "$reor"
run_step "Step 1 BET on reoriented T1" bet "$reor" "${prefix}_T1_bet" -R -f 0.4 -B
run_step "Step 2 FAST" fast -R 0.3 -H 0.1 -o "${prefix}_seg" "${prefix}_T1_bet.nii.gz"
run_step "Step 3 FLIRT T1_bet to MNI brain" flirt \
  -in "${prefix}_T1_bet.nii.gz" \
  -ref "$ref_brain" \
  -dof 12 \
  -omat "${prefix}_linear.mat" \
  -out "${prefix}_T1_flirt.nii.gz"
run_step "Step 4 Apply affine to native GM PVE" flirt \
  -in "${prefix}_seg_pve_1.nii.gz" \
  -ref "$ref_brain" \
  -applyxfm \
  -init "${prefix}_linear.mat" \
  -interp trilinear \
  -out "${prefix}_GM_MNI.nii.gz"
run_step "Step 5 GM mask threshold" fslmaths "${prefix}_GM_MNI.nii.gz" -thr 0.15 -bin "${prefix}_GM_mask.nii.gz"
run_step "Step 6 Apply GM mask" fslmaths "${prefix}_GM_MNI.nii.gz" -mul "${prefix}_GM_mask.nii.gz" "${prefix}_GM_masked.nii.gz"

if [ "${KEEP_INTERMEDIATES:-0}" != "1" ]; then
  echo "--- cleanup | $(date) ---" >> "$log"
  rm -f \
    "$reor" \
    "${prefix}_T1_bet"* \
    "${prefix}_seg"* \
    "${prefix}_linear.mat" \
    "${prefix}_T1_flirt.nii.gz" \
    "${prefix}_GM_MNI.nii.gz" \
    "${prefix}_GM_mask.nii.gz"
fi

echo "end: $(date)" >> "$log"
echo "DONE GM_v2 ${prefix}_GM_masked.nii.gz"
