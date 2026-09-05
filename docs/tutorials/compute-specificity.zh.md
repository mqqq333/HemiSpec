# 计算特异性图

ANS/RNS 的定义见[ANS 与 RNS 指标](../methods/ans-rns-metrics.md)，其方法源自 Wang 等人（2024）。

本教程介绍重建后的 ANS/RNS 计算。

## 安装

使用当前源码检出。克隆前启用 Git LFS，使该检出也可用于模型驱动工作流：

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e "."
git rev-parse HEAD
```

请将输出的 commit 哈希与分析记录一同保存。旧版本仍可从 [GitHub Releases 页面](https://github.com/mqqq333/HemiSpec/releases)获取，但本教程面向当前 `main`。

如需完整的包内冒烟测试，可运行 `hemispec quickstart --out-dir hemispec_quickstart_run_001`；它会生成玩具配对输入并执行本页的计算路径。每次运行应使用新的输出目录。

## 所需配对输入

每个受试者需要一张实际目标灰质图和一张相同形状、仿射变换和方向的重建对应物。

## 当前命令

```bash
hemispec compute \
  --actual-glob "derivatives/*_GM_masked.nii.gz" \
  --predicted-glob "outputs/recon/*_PRED_LR_full.nii.gz" \
  --out-dir outputs/specificity_run_001 \
  --save-subject-maps
```

这会写入组级 ANS/RNS 图，使用 `--save-subject-maps` 时还会写入受试者级图，用于验证和 ROI 提取。

## ROI 导出

ROI 特征导出可通过 `compute` 选项实现。请提供位于指标图网格上的经批准本地 atlas，详见[数据与模型](../data-and-models.md)。将示例路径替换为实际 atlas 路径：

```bash
hemispec compute \
  --actual-glob "derivatives/*_GM_masked.nii.gz" \
  --predicted-glob "outputs/recon/*_PRED_LR_full.nii.gz" \
  --out-dir outputs/specificity_roi_run_001 \
  --roi-atlas /approved/path/atlas.nii.gz \
  --roi-out-csv outputs/specificity_roi_run_001/roi_features.csv
```

目前还没有独立的 `roi` 命令。

## 输出

- 受试者级 ANS 图。
- 受试者级 RNS 图。
- 可选 ROI 级特征表。
- 启用时的组级体素汇总。

## 计算前检查

`compute` 会检查配对文件之间的形状和 affine 是否一致，并将非有限值体素排除在有效掩膜之外。这些检查不能证明标准 MNI 对齐、正确的半球标识或解剖质量。计算前仍应按[输入与预处理](../input-preprocessing.md)核验体素大小、方向、完整模板 affine、配准、分割和掩膜质量。
