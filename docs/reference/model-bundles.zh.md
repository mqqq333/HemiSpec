# 模型包

HemiSpec 通过 Git LFS 在 `assets/models/` 下包含可复用的已发布模型参数，wheel/PyPI 安装可将相同文件下载到每用户缓存。源码检出时请使用 Git LFS；否则模型文件可能下载为小型指针文件。

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
```

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

每个指标文件夹包含可运行的 `*.joblib` 包以及 `feature_names.csv`。默认 GUI/API 分类器模式使用 `OUT_noICBM_train_ICBM_external_saved_models`；`paired_residual` 可通过 CLI/API 配置选择。

## 发现顺序

HemiSpec 按以下顺序解析模型路径：

1. 提供时的显式 CLI/API/GUI 路径；
2. 如 `HEMISPEC_DGN_MODEL_ROOT` 和 `HEMISPEC_CLASSIFIER_MODEL_DIR` 等环境变量；
3. `assets/models/` 下打包的源码检出路径；
4. 每用户缓存（`HEMISPEC_MODEL_CACHE`，或系统特定的 HemiSpec 缓存）。

如果 wheel/PyPI 安装中缺少已发布的默认值，启用模型的命令会在首次使用时从 GitHub 下载。显式预取：

```bash
hemispec models --install --with-classifier
```

## 发行说明

模型二进制文件通过 Git LFS 追踪。请将原始 MRI 数据、生成输出和私有稿件专用产物保留在仓库之外。额外的模型包应包含出处、兼容的 HemiSpec 版本、预处理假设、校验和、许可证和引用说明。
