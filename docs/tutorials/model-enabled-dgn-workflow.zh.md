# 模型驱动 DGN 工作流

PyPI 项目尚未公开。本页面向从 `main` 获取的当前源码检出；旧版本可从 [GitHub Releases 页面](https://github.com/mqqq333/HemiSpec/releases)获取。

本页记录使用 `assets/models/` 下由 Git LFS 追踪的可复用参数运行 HemiSpec 的当前模型驱动工作流。不分发真实 MRI 输入和生成输出。

## 状态

- **合成仅计算演示**：无需模型资产即可使用；见 [快速开始](../quickstart.md)。
- **模型驱动源码检出**：使用 Git LFS 克隆并从 PyTorch 环境运行时可用。
- **DGN 缓存下载**：当前 `main` 可从仓库 Git LFS media 下载缺失的 DGN 检查点；完整分类器包必须来自本地 Git LFS 检出或其他已批准的本地目录。

## 设置

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e ".[gui,model,classifier]"
git rev-parse HEAD
```

请将输出的 commit 哈希与分析记录一同保存。在 Windows 上，请从包含所需 PyTorch/CUDA 构建的 conda 环境运行上述命令。

## 打包模型布局

```text
assets/models/dgn/
  outputs_bi_stable_L/ckpts/best_netG_L.pth
  outputs_bi_stable_R/ckpts/best_netG_R.pth
assets/models/hemisphere_classifier/
  OUT_noICBM_train_ICBM_external_saved_models/
  OUT_noICBM_train_ICBM_external_saved_models_paired_residual/
```

HemiSpec 会自动发现此源码检出布局。`HEMISPEC_DGN_MODEL_ROOT` 和 `HEMISPEC_CLASSIFIER_MODEL_DIR` 可选择其他已批准的本地资产。当前 `main` 可通过 `hemispec models --install` 填充 DGN 缓存；不要把 `--with-classifier` 作为安装方法，因为必需的 `feature_names.csv` media URL 当前返回 HTTP 404。详见[数据与模型](../data-and-models.md)。

## GUI 路径

启动 GUI：

```bash
hemispec-gui
python scripts/hemispec_gui_entry.py  # 等效的源码检出入口
```

设置状态卡报告：

- DGN 模型：已找到 / 未找到；
- Glasser atlas：已找到 / 未找到；
- 分类器包：已找到 / 未找到；
- PyTorch：可用 / 未找到。

选择包含 `*_GM_masked.nii.gz` 文件的文件夹或如 `derivatives/*_GM_masked.nii.gz` 的 glob，选择输出工作区，然后点击 **运行 HemiSpec**。日志打印每个文件的推理、计算和合并进度；**停止** 在当前文件完成后请求取消。

ROI 表导出是可选的。任意与输入网格一致的 atlas 可用于仅 ROI 导出。已发布分类器明确要求兼容的 Glasser 1.5 mm atlas 和标签表，左侧标签为 `1..180`，右侧为 `1001..1180`。仅需体素级/受试者级 ANS/RNS 图时取消勾选 **导出 ROI 表**。

## CLI 路径

首先确认 HemiSpec 发现了两个 DGN 方向：

```bash
hemispec models
```

然后在已批准的预处理灰质图上运行标准双向工作流：

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_workflow_run_001
```

分类器验证要求兼容的 Glasser 资产；不要替换为自定义 atlas：

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_classifier_run_001 \
  --roi-atlas "$HEMISPEC_GLASSER_ATLAS" \
  --roi-label-table "$HEMISPEC_GLASSER_LABEL_TABLE" \
  --classifier-model-dir "assets/models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models" \
  --run-classifier
```

TRT 至少需要 2 名受试者、每名 2 次扫描。例如准备 `sub-001_run-01_GM_masked.nii.gz`、`sub-001_run-02_GM_masked.nii.gz`，以及 `sub-002` 的对应文件；然后明确指定文件名解析器和 session 值：

```bash
hemispec workflow \
  --input-glob "derivatives/sub-*_run-*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_trt_run_001 \
  --run-trt \
  --trt-file-regex "(?P<subject>sub-[0-9]+)_(?P<session>run-[0-9]+)" \
  --trt-session-a run-01 \
  --trt-session-b run-02 \
  --keep-intermediate
```

TRT regex 应用于移除 `_GM_masked` 后的合并文件名，例如 `sub-001_run-01_ANS.nii.gz`。如果后续要将 `intermediate/combined_maps/` 传给独立验证，请使用 `--keep-intermediate`；方向特定图使用不同的后缀契约。每个示例都使用新的输出目录，因为工作流输出目录不应重复使用。

## 发布边界

仓库模型包让用户无需重新训练即可运行推理。它们不包括原始 MRI 数据、生成输出或私有稿件专用分析表。额外的公开资产应包含出处、校验和、兼容的 HemiSpec 版本、预处理假设和许可证/引用说明；见 [外部资产包](../reference/asset-bundle.md)。
