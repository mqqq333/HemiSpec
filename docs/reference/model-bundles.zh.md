# 模型包

HemiSpec 通过 Git LFS 在 `assets/models/` 下追踪可复用模型参数。请启用 Git LFS 后克隆当前 `main`；否则模型文件可能仍是小型指针文件。

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e ".[model,classifier]"
git rev-parse HEAD
```

请记录输出的 commit 哈希，以便后续识别代码和模型检出。

## 打包的 DGN 检查点

```text
assets/models/dgn/
  outputs_bi_stable_L/ckpts/best_netG_L.pth
  outputs_bi_stable_R/ckpts/best_netG_R.pth
```

这些是 `hemispec workflow` 和 GUI 使用的双向生成器检查点。训练中间文件、判别器检查点和重建预览不随软件分发。

## 打包的分类器模型

```text
assets/models/hemisphere_classifier/
  OUT_noICBM_train_ICBM_external_saved_models/
  OUT_noICBM_train_ICBM_external_saved_models_paired_residual/
```

每个指标文件夹包含已清理的运行时 `*_model_bundle.joblib`、训练完成的 `*_final_pipeline.joblib` 和 `feature_names.csv`。公开模型包不包含队列标识、样本量、评估指标、训练报告或私有出处路径。默认 GUI/API 分类器模式使用 `OUT_noICBM_train_ICBM_external_saved_models`；`paired_residual` 可通过 CLI/API 配置选择。

已发布分类器要求兼容的 Glasser 1.5 mm atlas 和标签表，每侧包含 180 个同源脑区：左侧标签为 `1..180`，右侧为 `1001..1180`。自定义 atlas 仅支持 ROI 导出，不能与已发布分类器配合使用。

## 发现顺序

HemiSpec 按以下顺序解析模型路径：

1. 提供时的显式 CLI/API/GUI 路径；
2. 如 `HEMISPEC_DGN_MODEL_ROOT` 和 `HEMISPEC_CLASSIFIER_MODEL_DIR` 等环境变量；
3. `assets/models/` 下打包的源码检出路径；
4. 每用户缓存（`HEMISPEC_MODEL_CACHE`，或系统特定的 HemiSpec 缓存）。

当前 `main` 可以把缺失的 DGN 检查点从仓库 Git LFS media 下载到用户缓存。显式预取这些检查点：

```bash
hemispec models --install
```

虽然 `hemispec models` 仍提供 `--with-classifier`，但当前分类器缓存下载不完整，因为必需的 `feature_names.csv` media URL 返回 HTTP 404。请改用 Git LFS 检出中的分类器资产或显式本地目录；详见[数据与模型](../data-and-models.md)。

## 发行说明

模型二进制文件通过 Git LFS 追踪。请将原始 MRI 数据、生成输出和私有稿件专用产物保留在仓库之外。额外的模型包应包含出处、兼容的 HemiSpec 版本、预处理假设、校验和、许可证和引用说明。

实现细节见[DGN 模型包](../developer/dgn-model-bundle.md)。ANS/RNS 与跨半球 DGN 框架源自 Wang 等人（2024）。
