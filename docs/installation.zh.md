# 安装

本文档支持的公开安装方式面向当前 `main` 源码树。软件包元数据仍显示版本 `0.1.0`，但 `main` 已包含旧 `v0.1.0` 标签及其归档软件包中没有的功能。`hemispec-toolkit` 项目当前尚未在 PyPI 公开。

## 推荐的源码安装

必须使用 Git LFS 获取 `assets/models/` 下跟踪的模型文件：

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e ".[gui,model,classifier]"
git rev-parse HEAD
```

每次分析都应记录 `git rev-parse HEAD` 的输出。仅记录分支名和软件包版本无法可复现地标识源码修订。

PyTorch 必须安装在启动 HemiSpec 的同一 Python 或 conda 环境中。运行模型前，请先配置合适的 CPU 或 CUDA PyTorch 构建。

源码检出中的 DGN 和分类器资产直接从 `assets/models/` 使用。进行分类器验证时，请使用这些本地分类器资产，或显式指定经批准的本地分类器目录；推荐安装流程不依赖缓存预下载。

## 归档的 v0.1.0 发布

GitHub [`v0.1.0` 发布](https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0)归档了原始 wheel、源码发行包和 Windows 产物。它是历史发布，不包含当前 `main` 的全部功能。具体而言，`v0.1.0` 标签不包含当前的合成快速入门或模型缓存下载模块。

下载归档 wheel 后，可以检查其基础 CLI：

```bash
python -m pip install ./hemispec_toolkit-0.1.0-py3-none-any.whl
hemispec --help
```

不要用归档 wheel 作为当前快速入门、模型发现或模型下载文档的安装方式。准确的归档内容见[发布产物](release-artifacts.md)。

## 开发安装

在当前源码检出中运行：

```bash
python -m pip install -e ".[dev,gui]"
python -m pytest
python -m ruff check src tests
python -m mkdocs build --strict
```

发行名为 `hemispec-toolkit`，导入路径和 CLI 命令为 `hemispec`。只有当项目实际在 PyPI 公开后，文档才能提供 PyPI 安装命令。

## 神经影像前置条件

启用模型的工作流从预处理 GM 图开始，不能直接输入原始 T1。仓库脚本依赖 BET、FAST、FLIRT 和 `fslmaths` 等 FSL 工具，以生成 MNI152 1.5 mm 的 `*_GM_masked.nii.gz` 输入。

处理真实数据前，请阅读[输入与预处理](input-preprocessing.md)。

## GUI 与模型运行时

请从包含 PyTorch 的源码环境启动 `hemispec-gui`。HemiSpec 可从显式路径、环境变量、`assets/models/` 下的 Git-LFS 检出或每用户缓存发现资产。Wheel 和轻量 Windows 产物不嵌入 PyTorch 或 300 MB 以上的 DGN 检查点。当前资产边界见[数据与模型](data-and-models.md)。
