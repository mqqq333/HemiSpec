# 快速开始

本页展示当前 HemiSpec 工作流。公开品牌名称、CLI 示例和 Python API 均统一使用 HemiSpec 命名。

CLI 示例已于 2026-06-29 与当前工具包接口核对。公开包名为 `hemispec-toolkit`；导入路径和命令保持为 `hemispec`。

!!! note "命令命名"
    命令行界面使用 `hemispec`，图形界面使用 `hemispec-gui`。

!!! note "已发布模型资产"
    源码仓库通过 Git LFS 包含可复用的 DGN 检查点和半球分类器包。Wheel/PyPI 安装将这些大型二进制文件保存在 wheel 之外，首次模型运行时自动下载已发布的资产到用户缓存。无需重新训练。

## 公开安全的合成计算演示

如需不使用私有 MRI 数据、模型权重或 atlas 资产的首次 CLI 冒烟测试，可使用 HemiSpec Toolkit 合成快速入门。它会创建玩具 NIfTI 文件、模拟重建输出和玩具 atlas，然后运行带受试者图和 ROI 导出的 `hemispec compute`：

```powershell
cd <hemispec-toolkit-checkout>
python -m pip install -e .
powershell -ExecutionPolicy Bypass -File examples\synthetic_quickstart\run_synthetic_quickstart.ps1 -Python python
```

生成的图不是解剖数据，仅用于验证公开命令/文件契约。

## 启用模型的安装

对于 PyPI/wheel 安装，使用模型运行时额外依赖，并可选择预下载已发布的模型资产：

```bash
python -m pip install "hemispec-toolkit[gui,model,classifier]"
hemispec models --install --with-classifier
hemispec-gui
```

如果跳过 `hemispec models --install`，首次 `hemispec workflow`、`hemispec infer`、`hemispec run` 或 GUI 模型运行时会自动下载已发布的 DGN 检查点。

对于 Git-LFS 源码检出，从仓库安装：

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e .[gui,model,classifier]
python scripts/hemispec_gui_entry.py
```

Git LFS 检出或模型缓存下载后，GUI 设置卡应显示 DGN 模型和分类器包已找到。PyTorch 可用性取决于启动 GUI 所用的 Python/conda 环境。

故障排除：如果分类器验证报告 `No module named 'numpy._core'`，请更新到最新的 HemiSpec 检出。运行时包含兼容 shim，可让旧版 conda 环境加载用 NumPy 2.x 保存的分类器包。

## 1. 准备灰质图

在 T1 加权 MRI 数据上运行预处理工作流以生成掩膜灰质图。工具包将参考预处理脚本打包在 `src/hemispec/resources/preprocess/` 下；实际预处理仍依赖本地 FSL 安装和经过验证的站点特定假设：

```bash
bash src/hemispec/resources/preprocess/process_single_subject_GM_v2_reorient.sh \
  input_T1.nii.gz \
  derivatives/sub-001
```

预期输出：

```text
derivatives/sub-001_GM_masked.nii.gz
```

## 2. 运行标准 GUI 工作流

从已安装 PyTorch 的同一环境启动启动器：

```bash
python -m pip install -e .[gui,model,classifier]
python scripts/hemispec_gui_entry.py
```

GUI 是一个精简的标准工作流界面。其设置状态卡在长时间运行前报告 DGN 模型、Glasser atlas 文件、分类器包和 PyTorch 是否已找到。普通用户选择：

1. **输入 GM 图**：如 `derivatives/*_GM_masked.nii.gz` 的 glob。
2. **输出工作区**：最终 voxel_maps/、tables/ 和可选 validation/ 输出写入位置。默认会删除重建文件，除非保留中间输出。
3. **可选 ROI 表**：atlas NIfTI 和标签表，有本地 Glasser 资产时默认使用。
4. **可选验证**：半球分类器验证和 TRT 可靠性。
5. **运行 HemiSpec**：GUI 显示等效的 `hemispec workflow` 命令以便复现。

主要输出是每个受试者四张体素级图：voxel_maps/ 下的 ANS.L、ANS.R、RNS.L 和 RNS.R。ROI 表是可选的下游功能，分类器验证需要 ROI 表导出。

## 3. 检查已打包的模型包

```bash
hemispec models
```

当 Git-LFS 检出或用户缓存包含已发布检查点时，此命令列出两个 DGN 方向。从 wheel/PyPI 安装预下载，运行 `hemispec models --install --with-classifier`。发布或分发额外训练权重前，请参阅 [数据与模型](data-and-models.md)。

## 4. 通过 CLI 运行双向工作流

GUI 映射到相同的公开 CLI/API 路径：

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_workflow
```

使用自定义 atlas 的可选 ROI 表：

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_workflow \
  --roi-atlas atlas/custom_atlas.nii.gz \
  --roi-label-table atlas/custom_labels.xlsx
```

仅需体素级图时跳过 ROI 表导出：

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_workflow \
  --no-roi-table
```

## 5. 底层 CLI 命令

单方向 DGN 推理：

```bash
hemispec infer \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --direction L_to_R \
  --out-dir outputs/recon_L_to_R
```

从已有实际图和重建图计算 ANS/RNS：

```bash
hemispec compute \
  --actual-glob "derivatives/*_GM_masked.nii.gz" \
  --predicted-glob "outputs/recon_L_to_R/*_PRED_LR_full.nii.gz" \
  --out-dir outputs/specificity_L_to_R \
  --save-subject-maps
```

单方向推理和计算一起运行：

```bash
hemispec run \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --direction L_to_R \
  --recon-dir outputs/recon_L_to_R \
  --metrics-dir outputs/specificity_L_to_R
```

## 6. 验证图

对于标准工作流，建议在工作流运行时启用验证，以便结果写入可预测的文件夹：

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_workflow \
  --run-classifier \
  --run-trt
```

这会将分类器输出写入 `outputs/hemispec_workflow/validation/hemi_classify/`，将 TRT 输出写入 `outputs/hemispec_workflow/validation/trt/`。

## 尚未就绪的功能

- 独立的 `report` 命令。
- 独立的 `roi` 命令。
- 公开的真实数据预处理资产和批准的真实样本数据。
- 任何尚未获批的 atlas 有效载荷的公开再发行决定。
- 完全公开的利手性复现工作流。
