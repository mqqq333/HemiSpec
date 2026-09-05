# GUI 用户指南

安装包提供的 `hemispec-gui` 命令用于启动标准 HemiSpec 双向工作流。请从同时安装了 HemiSpec 和 PyTorch 的同一 Python 环境启动。

## 启动

从 `main` 的 Git LFS 源码检出安装当前 GUI：

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e ".[gui,model,classifier]"
git rev-parse HEAD
hemispec-gui
```

请将输出的 commit 哈希与分析记录一同保存。当前 PyPI 项目尚未公开，本指南不使用已归档的 v0.1.0 wheel。旧版本仍可从 [GitHub Releases 页面](https://github.com/mqqq333/HemiSpec/releases)获取。

## 打开 GUI 前

每名受试者应准备一张 DGN 可用的 GM 图。原始 T1 加权图像必须先通过 FSL 预处理：

```text
T1 加权 NIfTI -> process_single_subject.sh -> *_GM_masked.nii.gz
```

详见[输入与预处理](../input-preprocessing.md)。

## 六个 GUI 卡片

### 1. 输入 GM 图

选择目录，或输入类似下面的 glob：

```text
derivatives/*_GM_masked.nii.gz
```

### 2. 输出工作区

每次运行选择一个新的空输出目录。最终图写入 `voxel_maps/`，表格和可选验证结果写入各自子目录。

### 3. 设置状态

确认 PyTorch 和两个 DGN 方向可用。Atlas 和分类器仅在启用对应选项时才是必需项。

### 4. 可选 ROI 表

仅在具有 atlas 和兼容标签表时启用 ROI 导出。Atlas 必须与输入图具有相同网格和 affine。自定义 atlas 可用于仅 ROI 导出；已发布分类器则要求兼容的 Glasser 1.5 mm atlas，左侧标签为 `1..180`，右侧为 `1001..1180`。

### 5. 可选验证

- **半球分类器验证**需要兼容的 Glasser ROI 特征，以及 Git LFS 检出中的本地分类器包。当前分类器缓存下载不完整；详见[数据与模型](../data-and-models.md)。
- **TRT 可靠性**至少需要 2 名受试者、每名 2 次扫描。GUI 使用封装的默认模式，例如 `sub-MSC001_run-01_GM_masked.nii.gz` 和 `sub-MSC001_run-02_GM_masked.nii.gz`；如果文件名为 `sub-001_run-01_GM_masked.nii.gz` 并需要显式 regex/session 参数，请使用 CLI。
- **保留中间输出**会保存用于调试的重建图和方向特定图，并保存供后续独立验证使用的 `intermediate/combined_maps/`。方向特定图使用不同的后缀契约。

### 6. 运行控制

检查或复制等效 CLI 命令，启动或停止工作流，查看日志，并打开输出目录。

## 可复现性

将 GUI 显示的 CLI 命令连同 HemiSpec commit/版本、预处理脚本版本、模型包、atlas 版本和已启用的可选验证步骤一起记录到研究方案中。

ANS/RNS 与跨半球 DGN 框架源自 Wang 等人（2024），详见[引用](../citation.md)。
