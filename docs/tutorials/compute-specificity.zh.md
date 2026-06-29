# 计算特异性图

本教程介绍重建后的 ANS/RNS 计算。

## 所需配对输入

每个受试者需要一张实际目标灰质图和一张相同形状、仿射变换和方向的重建对应物。

## 当前命令

```bash
hemispec compute \
  --actual-glob "derivatives/*_GM_masked.nii.gz" \
  --predicted-glob "outputs/recon/*_PRED_LR_full.nii.gz" \
  --out-dir outputs/specificity \
  --save-subject-maps
```

这会写入组级 ANS/RNS 图，使用 `--save-subject-maps` 时还会写入受试者级图，用于验证和 ROI 提取。

## ROI 导出

ROI 特征导出可通过 `compute` 选项实现。在添加公开 HemiSpec atlas 资产或记录外部 atlas 安装之前，atlas 路径为占位符：

```bash
hemispec compute \
  --actual-glob "derivatives/*_GM_masked.nii.gz" \
  --predicted-glob "outputs/recon/*_PRED_LR_full.nii.gz" \
  --out-dir outputs/specificity \
  --roi-atlas <atlas路径> \
  --roi-out-csv outputs/roi_features.csv
```

目前还没有独立的 `roi` 命令。

## 输出

- 受试者级 ANS 图。
- 受试者级 RNS 图。
- 可选 ROI 级特征表。
- 启用时的组级体素汇总。

## 计算前检查

HemiSpec 在写入输出之前应验证形状、仿射变换、有限值、半球标签和有效掩膜。
