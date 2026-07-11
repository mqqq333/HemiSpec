# GUI 用户指南

安装包提供的 `hemispec-gui` 命令用于启动标准 HemiSpec 双向工作流。请从同时安装了 HemiSpec 和 PyTorch 的同一 Python 环境启动。

## 启动

从源码检出安装：

```bash
python -m pip install -e .[gui,model,classifier]
hemispec-gui
```

从 v0.1.0 Release wheel 安装：

```bash
python -m pip install "./hemispec_toolkit-0.1.0-py3-none-any.whl[gui,model,classifier]"
hemispec-gui
```

当前 PyPI 项目尚未公开，请使用 GitHub Release wheel 或源码检出。

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

选择新的或已有的输出目录。最终图写入 `voxel_maps/`，表格和可选验证结果写入各自子目录。

### 3. 设置状态

确认 PyTorch 和两个 DGN 方向可用。Atlas 和分类器仅在启用对应选项时才是必需项。

### 4. 可选 ROI 表

仅在具有 atlas 和兼容标签表时启用 ROI 导出。Atlas 必须与输入图具有相同网格和 affine。

### 5. 可选验证

- **半球分类器验证**需要 ROI 特征，并保持为可选步骤。
- **TRT 可靠性**要求文件名符合配置的 session 正则表达式。
- **保留中间输出**会保存重建图和方向特定图，用于调试或独立验证。

### 6. 运行控制

检查或复制等效 CLI 命令，启动或停止工作流，查看日志，并打开输出目录。

## 可复现性

将 GUI 显示的 CLI 命令连同 HemiSpec commit/版本、预处理脚本版本、模型包、atlas 版本和已启用的可选验证步骤一起记录到研究方案中。

ANS/RNS 与跨半球 DGN 框架源自 Wang 等人（2024），详见[引用](../citation.md)。
