# 数据与模型

HemiSpec 运行启用模型的工作流需要两类外部资产：**DGN 模型权重**和用于 ROI 导出的 **atlas 文件**。这两类资产均不包含在 Python wheel 或轻量桌面应用中。

## 模型权重

HemiSpec 使用两个训练好的 DGN 生成器检查点（每个半球方向各一个）和可选的半球分类器包。

**源码检出（Git LFS）**

使用 LFS 克隆以直接获取模型文件：

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
```

**Wheel / PyPI 安装**

首次启用模型的运行时自动下载模型：

```bash
python -m pip install "hemispec-toolkit[model,classifier]"
hemispec workflow --input-glob "derivatives/*_GM_masked.nii.gz" --out-dir outputs/
```

显式预下载：

```bash
hemispec models --install --with-classifier
```

下载的文件存储在 HemiSpec 用户缓存中（`HEMISPEC_MODEL_CACHE`，或系统默认缓存目录）。

## Atlas 文件

ROI 表格导出需要 MNI 空间的脑区分割 atlas。HemiSpec 在 GitHub release 中提供了 Glasser HCP-MMP atlas 作为开箱即用的默认选项，你也可以使用任意相同格式的 atlas。

**下载内置 Glasser atlas**

从 [HemiSpec v0.1.0 release](https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0) 下载 `MNI_Glasser_HCP_v1.0_1p5mm.nii.gz` 和 `Glasser_label_index_mapping.xlsx`。

通过环境变量一次性设置路径：

```bash
export HEMISPEC_GLASSER_ATLAS=/path/to/MNI_Glasser_HCP_v1.0_1p5mm.nii.gz
export HEMISPEC_GLASSER_LABEL_TABLE=/path/to/Glasser_label_index_mapping.xlsx
```

**使用自定义 atlas**

直接传入任意 NIfTI atlas 和标签表：

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/ \
  --roi-atlas /path/to/atlas.nii.gz \
  --roi-label-table /path/to/labels.xlsx
```

ROI 导出是可选的。未提供 atlas 时，仍会生成体素级 ANS/RNS 图。

## 不分发的内容

真实 MRI 数据和生成输出不随 HemiSpec 分发。公开仓库仅包含代码、文档、测试、合成示例，以及通过 Git LFS 追踪的已批准可复用模型包。

## 归因

ANS/RNS 指标和跨半球 DGN 框架源自 Wang 等人 2024 年 *Patterns* 论文。HemiSpec 在此基础上打包并扩展了该工作流。
