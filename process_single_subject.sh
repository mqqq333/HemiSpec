#!/bin/bash

# 参数检查
if [ $# -ne 2 ]; then
  echo "用法: $0 输入文件.nii.gz 输出前缀" | tee -a "${2}_debug.log"
  exit 1
fi

input=$1
prefix=$2

# 打印开始时间
echo "脚本开始时间: $(date)" >> "${prefix}_debug.log"

# Step 1: 颅骨剥离
echo "Step 1: 颅骨剥离 (BET)" >> "${prefix}_debug.log"
echo "Running BET for $input" >> "${prefix}_debug.log"


bet "$input" "${prefix}_T1_bet" -f 0.4 -B


if [ $? -ne 0 ]; then
  echo "BET失败: $input" >> "${prefix}_debug.log"
  exit 1
fi
echo "BET完成" >> "${prefix}_debug.log"

# Step 2: 组织分割
echo "Step 2: 组织分割 (FAST)" >> "${prefix}_debug.log"
fast -R 0.3 -H 0.1 -o "${prefix}_seg" "${prefix}_T1_bet.nii.gz"
if [ $? -ne 0 ]; then
  echo "FAST失败: ${prefix}_T1_bet.nii.gz" >> "${prefix}_debug.log"
  exit 1
fi
echo "FAST完成" >> "${prefix}_debug.log"

# Step 3: MNI空间标准化
echo "Step 3: MNI标准化 (FLIRT)" >> "${prefix}_debug.log"
flirt -in "${prefix}_seg_pve_1.nii.gz" \
  -ref "${FSLDIR}/data/standard/MNI152_T1_1.5mm_brain.nii.gz" \
  -omat "${prefix}_linear.mat" \
  -out "${prefix}_GM_linear_MNI"

if [ $? -ne 0 ]; then
  echo "FLIRT失败: ${prefix}_seg_pve_1.nii.gz" >> "${prefix}_debug.log"
  exit 1
fi
echo "FLIRT完成" >> "${prefix}_debug.log"

# Step 4: 灰质掩模
echo "Step 4: 灰质掩模 (fslmaths)" >> "${prefix}_debug.log"
fslmaths "${prefix}_GM_linear_MNI.nii.gz" -thr 0.15 -bin "${prefix}_GM_mask.nii.gz"
if [ $? -ne 0 ]; then
  echo "fslmaths (阈值处理)失败: ${prefix}_GM_linear_MNI.nii.gz" >> "${prefix}_debug.log"
  exit 1
fi
fslmaths "${prefix}_GM_linear_MNI.nii.gz" -mul "${prefix}_GM_mask.nii.gz" "${prefix}_GM_masked.nii.gz"
if [ $? -ne 0 ]; then
  echo "fslmaths (掩模应用)失败: ${prefix}_GM_linear_MNI.nii.gz" >> "${prefix}_debug.log"
  exit 1
fi
echo "fslmaths完成" >> "${prefix}_debug.log"

# Step 5: 半球处理
# echo "Step 5: 半球分割 (已注释)" >> "${prefix}_debug.log"
# fslmaths "${prefix}_GM_masked.nii.gz" -roi 0 46 -1 -1 -1 -10 -1 "${prefix}_LH_GM.nii.gz"
# fslmaths "${prefix}_GM_masked.nii.gz" -roi 46 45 -1 -1 -1 -10 -1 "${prefix}_RH_GM.nii.gz"

# 清理中间文件 (保留关键输出)
echo "清理中间文件" >> "${prefix}_debug.log"
rm -f \
  "${prefix}_T1_bet"* \
  "${prefix}_seg"* \
  "${prefix}_linear.mat" \
  "${prefix}_GM_mask.nii.gz" \
  "${prefix}_GM_linear_MNI.nii.gz"

# 打印结束时间
echo "脚本结束时间: $(date)" >> "${prefix}_debug.log"

echo "处理完成: ${prefix}" >> "${prefix}_debug.log"
