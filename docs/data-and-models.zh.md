# 数据与模型

HemiSpec 涉及神经影像数据和训练好的模型权重，因此公开仓库采用保守的数据边界。

## 不要提交

- 原始 T1 加权 MRI 数据。
- 未经批准公开再发行的受试者级衍生数据。
- 大型 `.nii.gz`、`.pth`、`.pt`、`.ckpt`、`.joblib`、`.pkl` 或 `.xlsx` 有效载荷，除非是明确批准的发布产物并有意追踪。
- 公开发布批准前的仅供稿件使用的图表或表格。
- 私有工作站路径、服务器路径、密钥、令牌或仅供本地协调的备注。

## 仓库政策

源码仓库包含代码、文档、测试、合成示例和已批准的可复用模型包。`assets/models/` 下的大型二进制模型文件通过 Git LFS 追踪：

```text
assets/models/dgn/                       # 可复用的双向 DGN 生成器检查点
assets/models/hemisphere_classifier/     # 可复用的分类器包
assets/atlases/                          # atlas 有效载荷可能在本地/外部，除非明确发布
```

包 wheel 和默认 PyInstaller 规格保持轻量，不嵌入仓库级 `assets/`。启用模型的 CLI/GUI/API 运行可在本地检出/缓存为空时从 GitHub 仓库下载已发布的模型文件到每用户缓存。

## 打包模型布局

Git-LFS 源码检出提供以下模型布局：

```text
assets/models/dgn/
  outputs_bi_stable_L/ckpts/best_netG_L.pth
  outputs_bi_stable_R/ckpts/best_netG_R.pth
assets/models/hemisphere_classifier/
  OUT_noICBM_train_ICBM_external_saved_models/
  OUT_noICBM_train_ICBM_external_saved_models_paired_residual/
```

使用 `git lfs install` 和 `git lfs pull` 克隆；否则这些文件可能显示为小型 LFS 指针文本文件而非可用的模型二进制文件。

支持的环境变量：

```text
HEMISPEC_ASSET_ROOT
HEMISPEC_DGN_MODEL_ROOT
HEMISPEC_CLASSIFIER_MODEL_DIR
HEMISPEC_MODEL_CACHE
HEMISPEC_MODEL_ASSET_BASE_URL
HEMISPEC_AUTO_DOWNLOAD_MODELS
HEMISPEC_DISABLE_MODEL_AUTO_DOWNLOAD
HEMISPEC_GLASSER_ATLAS
HEMISPEC_GLASSER_LABEL_TABLE
```

GUI 和 CLI 的解析优先级：显式路径 > 环境变量 > 本地仓库约定 > 每用户缓存。即源码检出通常无需额外标志就能找到 `assets/models/dgn` 和默认分类器包；wheel/PyPI 安装在首次模型使用时将已发布的默认值下载到 `HEMISPEC_MODEL_CACHE`（或系统特定的 HemiSpec 缓存）。发布额外资产时的清单/校验和/许可证契约见 [外部资产包](reference/asset-bundle.md)。

## 外部发布渠道

推荐使用 GitHub Releases、Zenodo、OSF 或机构存储来发布模型权重和编译应用资产包。每个已发布的资产包应包含：

- 版本和日期，
- 来源/出处，
- 许可证和引用要求，
- 预期本地路径或环境变量，
- 校验和，
- 预处理假设，
- 兼容的 `hemispec-toolkit` 版本。

## 方法与模型归因

如果发布内容分发或记录具有 ANS/RNS 能力的模型或工作流，请明确保持方法边界：原始 ANS/RNS 指标和跨半球 DGN 框架来自 Wang 等人 2024 年 *Patterns* 论文。HemiSpec 为当前软件和利手性应用打包并扩展了该工作流。
