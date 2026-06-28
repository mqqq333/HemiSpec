# 输出文件说明

## Generate ANS/RNS / Full Workflow ??

`hemispec workflow` ? GUI ? `Generate ANS/RNS` ????????? GM ????????? DGN?????? voxel-wise / subject-level ANS/RNS ??????ROI table ???? atlas-derived ?????????? ROI table?TRT ???????

典型目录结构：

```text
recon/L_to_R/                              L -> R 的 DGN 重建 GM
recon/R_to_L/                              R -> L 的 DGN 重建 GM
metrics/L_to_R/                            L -> R 单方向 ANS/RNS 输出
metrics/R_to_L/                            R -> L 单方向 ANS/RNS 输出
subject_maps/<subject>_ANS.nii.gz          双侧合并 ANS map
subject_maps/<subject>_RNS.nii.gz          双侧合并 RNS map
subject_hemi_maps/<subject>_ANS.L.nii.gz   左半球 ANS
subject_hemi_maps/<subject>_ANS.R.nii.gz   右半球 ANS
subject_hemi_maps/<subject>_RNS.L.nii.gz   左半球 RNS
subject_hemi_maps/<subject>_RNS.R.nii.gz   右半球 RNS
tables/roi_features_bilateral.csv          ?? ROI-wise ??
tables/roi_features_bilateral_wide.csv     ?? ROI-wise ??
tables/subject_metric_summary.csv          被试级半球/全脑均值
hemisphere_classifier/                     ????????????
trt/                                       可选 TRT 输出
```

双向模型方向：

```text
L_to_R = left hemisphere -> generated right hemisphere
R_to_L = right hemisphere -> generated left hemisphere
```

## Voxel-wise 输出

`subject_maps/` 中每个被试有双侧合并 map：

```text
<subject>_ANS.nii.gz
<subject>_RNS.nii.gz
```

`subject_hemi_maps/` 中每个被试有四个半球单独 map：

```text
<subject>_ANS.L.nii.gz
<subject>_ANS.R.nii.gz
<subject>_RNS.L.nii.gz
<subject>_RNS.R.nii.gz
```

默认在有效区域外写入 NaN，这样均值统计会忽略无效体素。

## ROI-wise 输出

`tables/roi_features_bilateral.csv` 是长表，适合半球分类器使用。关键字段：

```text
subject       被试 ID
kind          ANS 或 RNS
hemi          L 或 R
roi_label     atlas 原始标签
roi_index     左右半球配对后的 ROI 编号
metric_hemi   ANS.L、ANS.R、RNS.L、RNS.R
feature_name  例如 ANS.L_roi_1
value         ROI 内统计值，默认 mean
n_voxels      参与统计的有限体素数
```

`tables/roi_features_bilateral_wide.csv` 是宽表，每个被试一行，列名显式区分指标和半球：

```text
subject
ANS.L_roi_1
ANS.R_roi_1
RNS.L_roi_1
RNS.R_roi_1
...
```

## Subject Summary

`tables/subject_metric_summary.csv` 每个被试一行：

```text
subject
ANS.L_mean
ANS.R_mean
RNS.L_mean
RNS.R_mean
ANS.whole_brain_mean
RNS.whole_brain_mean
```

其中 whole-brain mean 是双侧合并 map 中所有有限体素的均值。

## TRT / Specificity 输出

每个 `ANS/RNS x L/R` 会输出：

```text
similarity_ANS_L.csv
within_ANS_L.csv
summary_ANS_L.txt
heatmap_ANS_L.png
boxplot_ANS_L.png
validation_summary.csv
```

`validation_summary.csv` 主要字段：

```text
kind               ANS 或 RNS
hemi               L/R/ALL
n_subjects         具有完整 session A/B 的被试数
n_voxels           mask 后进入相似度计算的体素数
match_rate         top-1 match rate
specificity_index  within_mean - between_mean
cohen_d            within vs between 效应量
within_mean        同一被试跨 session 相似度均值
between_mean       不同被试相似度均值
t_value            Welch t-test 的 t
p_value            Welch t-test 的 p
```

TRT 和 structural specificity 使用同一相似度矩阵引擎；TRT 的解释重点是重测稳定性，specificity 的解释重点是个体结构区分度。
