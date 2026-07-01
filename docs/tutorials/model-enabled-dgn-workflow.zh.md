# 模型驱动 DGN 工作流

本页记录使用可复用已发布模型参数运行 HemiSpec 的当前模型驱动工作流。DGN 检查点和半球分类器包通过 Git LFS 追踪在 `assets/models/` 下；wheel/PyPI 安装可将相同文件下载到用户缓存。不分发真实 MRI 输入和生成输出。

## 状态

- **合成仅计算演示**：无需模型资产即可使用；见 [快速开始](../quickstart.md)。
- **模型驱动源码检出**：使用 Git LFS 克隆并从 PyTorch 环境运行时可用。
- **Wheel/PyPI / 轻量桌面安装**：通过首次运行将已发布检查点下载到用户缓存实现模型驱动；仍需在活动环境中安装 PyTorch。

## 设置

PyPI 安装：

```bash
python -m pip install "hemispec-toolkit[gui,model,classifier]"
hemispec models --install --with-classifier  # 可选预下载
```

源码检出：

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e .[gui,model,classifier]
```

在 Windows 上，请从包含所需 PyTorch/CUDA 构建的 conda 环境运行上述命令。

## 打包模型布局

```text
assets/models/dgn/
  outputs_bi_stable_L/ckpts/best_netG_L.pth
  outputs_bi_stable_R/ckpts/best_netG_R.pth
assets/models/hemisphere_classifier/
  OUT_noICBM_train_ICBM_external_saved_models/
  OUT_noICBM_train_ICBM_external_saved_models_paired_residual/
```

HemiSpec 自动发现此布局。Wheel/PyPI 安装在自动下载后在用户模型缓存中使用相同布局。仅当需要覆盖已发布默认值时才需要 `HEMISPEC_DGN_MODEL_ROOT` 或 `HEMISPEC_CLASSIFIER_MODEL_DIR`。

## GUI 路径

启动 GUI：

```bash
hemispec-gui                 # PyPI 安装
python scripts/hemispec_gui_entry.py  # 源码检出
```

设置状态卡报告：

- DGN 模型：已找到 / 未找到；
- Glasser atlas：已找到 / 未找到；
- 分类器包：已找到 / 未找到；
- PyTorch：可用 / 未找到。

选择包含 `*_GM_masked.nii.gz` 文件的文件夹或如 `derivatives/*_GM_masked.nii.gz` 的 glob，选择输出工作区，然后点击 **运行 HemiSpec**。日志打印每个文件的推理、计算和合并进度；**停止** 在当前文件完成后请求取消。

ROI 表导出是可选的。ROI atlas 和标签表路径是用于 ROI 汇总和分类器验证的参考文件；仅需体素级/受试者级 ANS/RNS 图时取消勾选 **导出 ROI 表**。

## CLI 路径

首先确认 HemiSpec 发现了两个 DGN 方向：

```bash
hemispec models
```

然后在已批准的预处理灰质图上运行标准双向工作流：

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_full_demo
```

带可选 ROI 表、分类器验证和 TRT 可靠性：

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_full_demo \
  --roi-atlas "$HEMISPEC_GLASSER_ATLAS" \
  --roi-label-table "$HEMISPEC_GLASSER_LABEL_TABLE" \
  --run-classifier \
  --run-trt
```

来自小型冒烟测试数据集的分类器/TRT 输出应视为连通性检查，而非模型性能证据。

## 发布边界

仓库模型包让用户无需重新训练即可运行推理。它们不包括原始 MRI 数据、生成输出或私有稿件专用分析表。额外的公开资产应包含出处、校验和、兼容的 HemiSpec 版本、预处理假设和许可证/引用说明；见 [外部资产包](../reference/asset-bundle.md)。
