# 输出

HemiSpec 的输出应具有足够的可预测性，以便用于下游统计、机器学习和稿件报告。

## 标准工作流布局

`hemispec workflow` 和 GUI 写入紧凑的用户界面布局。默认最终输出为每个受试者四张体素图，以及可选的表格和验证报告：

```text
<输出目录>/
  voxel_maps/
    <subject>_ANS.L.nii.gz
    <subject>_ANS.R.nii.gz
    <subject>_RNS.L.nii.gz
    <subject>_RNS.R.nii.gz
  tables/
    subject_metric_summary.csv
    roi_features_bilateral.csv          # 启用 ROI 导出且 atlas 可用时
    roi_features_bilateral_wide.csv     # 启用 ROI 导出且 atlas 可用时
  validation/
    hemi_classify/                      # 仅在启用 --run-classifier 时
    trt/                                # 仅在启用 --run-trt 时
```

DGN 重建和单方向指标是中间实现细节。默认会删除它们，因为拼接的实际/重建图对大多数用户来说是冗余的。要调试或对合并的双向图运行独立验证，请在 CLI 中使用 `--keep-intermediate` 或 GUI 中的对应复选框：

```text
<输出目录>/
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
```

底层命令保留各自的历史契约。例如，`hemispec compute --save-subject-maps` 仍在其选择的输出目录下的 `subject_maps/` 中写入 `<subject>_ANS.nii.gz` 和 `<subject>_RNS.nii.gz`。

## 所需元数据路线图

每次运行最终应记录：

- HemiSpec 版本。
- 模型包版本。
- 输入路径或数据集标识符。
- 主要参数。
- 输出路径。
- 警告和验证失败。

这个完整的清单契约是计划中的功能；在实现之前不应将其描述为已完成。
