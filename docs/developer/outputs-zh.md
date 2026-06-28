# 输出文件说明

## 标准 workflow 输出

`hemispec workflow` 和 GUI 的 **Run HemiSpec** 按钮都会运行同一个标准流程。输入是预处理后的 GM maps，输出是双向 DGN reconstruction、voxel-wise / subject-level ANS/RNS maps，以及可选的 ROI table、classifier validation 和 TRT reliability 结果。

典型目录结构如下：

```text
<out-dir>/
  recon/
    L_to_R/
    R_to_L/
  metrics/
    L_to_R/
    R_to_L/
  subject_maps/
    <subject>_ANS.nii.gz
    <subject>_RNS.nii.gz
  subject_hemi_maps/
    <subject>_ANS.L.nii.gz
    <subject>_ANS.R.nii.gz
    <subject>_RNS.L.nii.gz
    <subject>_RNS.R.nii.gz
  tables/
    subject_metric_summary.csv
    roi_features_bilateral.csv
    roi_features_bilateral_wide.csv
  hemisphere_classifier/
  trt/
```

其中 `subject_maps/` 和 `subject_hemi_maps/` 是主要输出。ROI table、classifier 和 TRT 都是可选的下游输出。

## 主要 ANS/RNS map

每个被试会生成：

```text
subject_maps/<subject>_ANS.nii.gz
subject_maps/<subject>_RNS.nii.gz
```

这些文件是 voxel-wise 的 ANS/RNS 结果。用户可以直接用自己的 ROI、mask 或统计流程继续分析。

## Hemisphere-specific map

为了方便检查左右半球结果，流程也会写出：

```text
subject_hemi_maps/<subject>_ANS.L.nii.gz
subject_hemi_maps/<subject>_ANS.R.nii.gz
subject_hemi_maps/<subject>_RNS.L.nii.gz
subject_hemi_maps/<subject>_RNS.R.nii.gz
```

## ROI-wise 输出

当 ROI table 启用且 atlas 可用时，会生成两个表：

```text
tables/roi_features_bilateral.csv
tables/roi_features_bilateral_wide.csv
```

`roi_features_bilateral.csv` 是长表，适合 classifier adapter 使用。关键字段包括：

```text
subject
kind
roi_label
hemi
roi_index
metric_hemi
feature_name
value
```

`roi_features_bilateral_wide.csv` 是宽表，每个被试一行，列名显式区分指标和半球，例如：

```text
ANS.L_roi_1
ANS.R_roi_1
RNS.L_roi_1
RNS.R_roi_1
```

## Subject summary

`tables/subject_metric_summary.csv` 记录每个被试的左右半球和全脑均值，用于快速质量检查。

## Validation 输出

如果启用 hemisphere-classifier validation，会在 `hemisphere_classifier/` 下输出预测表和 summary。

如果启用 TRT reliability，会在 `trt/` 下输出 reliability summary 和可选图表。

## 公开发布注意事项

不要把真实被试 NIfTI、模型权重、classifier bundle、atlas payload 或未公开结果表提交到 git。公开仓库只保留代码、文档、测试、合成示例和 manifest；真实资产应通过独立 release bundle 分发。

