# 输出文件说明

## 标准 workflow 输出

hemispec workflow 和 GUI 的 Run HemiSpec 按钮运行同一个标准流程。用户输入预处理后的 GM maps，HemiSpec 自动运行双向 DGN、计算 ANS/RNS，并按用户选择输出 ROI table、hemisphere-classifier validation 和 TRT reliability。

默认情况下，面向用户保留的是最终结果；DGN reconstruction 和单方向中间 metrics 会被删除，因为这些一个真实半球加一个重建半球的拼接 recon 对最终分析比较冗余。

典型目录结构如下：

    <out-dir>/
      voxel_maps/
        <subject>_ANS.L.nii.gz
        <subject>_ANS.R.nii.gz
        <subject>_RNS.L.nii.gz
        <subject>_RNS.R.nii.gz
      tables/
        subject_metric_summary.csv
        roi_features_bilateral.csv
        roi_features_bilateral_wide.csv
      validation/
        hemi_classify/
        trt/

其中 voxel_maps/ 是主要输出。tables/ 中的 ROI table 需要 atlas；validation/hemi_classify/ 只在启用 classifier 时生成；validation/trt/ 只在启用 TRT 时生成。

如果需要调试或保留中间结果，在 CLI 使用 --keep-intermediate，或在 GUI 勾选 Keep intermediate reconstructions and one-direction metrics。此时会额外保留：

    <out-dir>/
      intermediate/
        recon/
          L_to_R/
          R_to_L/
        direction_metrics/
          L_to_R/
          R_to_L/
        combined_maps/
          <subject>_ANS.nii.gz
          <subject>_RNS.nii.gz

## 主要 voxel-wise ANS/RNS map

每个被试默认生成 4 个 voxel-wise map：

    voxel_maps/<subject>_ANS.L.nii.gz
    voxel_maps/<subject>_ANS.R.nii.gz
    voxel_maps/<subject>_RNS.L.nii.gz
    voxel_maps/<subject>_RNS.R.nii.gz

.L 表示左半球结果，.R 表示右半球结果。用户可以直接用这些 NIfTI 文件做自己的 ROI、mask、统计或可视化分析。

## ROI-wise 输出

当 ROI table 启用且 atlas 可用时，会生成两个表：

    tables/roi_features_bilateral.csv
    tables/roi_features_bilateral_wide.csv

roi_features_bilateral.csv 是长表，适合 classifier adapter 使用。关键字段包括：

    subject
    kind
    map_hemi
    roi_label
    hemi
    output_hemi
    roi_index
    metric_hemi
    feature_name
    value

roi_features_bilateral_wide.csv 是宽表，每个被试一行，列名显式区分指标和半球，例如：

    ANS.L_roi_1
    ANS.R_roi_1
    RNS.L_roi_1
    RNS.R_roi_1

## Subject summary

tables/subject_metric_summary.csv 记录每个被试的左右半球均值，并保留 ANS/RNS 的 whole-brain finite-voxel 均值，便于快速质量检查。

## Validation 输出

如果启用 hemisphere-classifier validation，会在 validation/hemi_classify/ 输出预测表和 summary。

如果启用 TRT reliability，会在 validation/trt/ 输出 reliability summary 和可选图表。

## 公开发布注意事项

公开仓库可以包含已批准发布的模型权重、代码、文档、测试、合成示例和 manifest。不要把真实被试 NIfTI、未公开结果表或未清理的本地绝对路径提交到 git。
