# 安装

HemiSpec 采用 PyPI 优先的安装方式。请将 Python 包安装到用于运行 PyTorch 和访问模型缓存的环境中；`hemispec` CLI 和 `hemispec-gui` 启动器都由该包创建。编译桌面文件夹和 GitHub Release wheel 主要作为备用或归档产物。

## 推荐：从 PyPI 创建启用模型的环境

在计划用于推理的 Python/conda 环境中，从 PyPI 安装已发布包及运行时额外依赖，并可选择预先下载已发布的模型资产到用户缓存：

```bash
python -m pip install "hemispec-toolkit[gui,model,classifier]"
hemispec models --install --with-classifier
hemispec-gui
```

如果跳过预下载命令，首次启用模型的 CLI/GUI/API 运行时会自动下载已发布的 DGN 检查点。启用分类器验证时，分类器包会自动下载。

如需获取仓库中的 DGN 和分类器模型，可使用 Git-LFS 源码检出：

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e .[gui,model,classifier]
python scripts/hemispec_gui_entry.py
```

在 Windows 上，请从包含目标 PyTorch 构建的 conda 或虚拟环境中运行 HemiSpec。如需 GPU/CUDA，先在该环境中配置 PyTorch，再安装或运行 HemiSpec。

## 基础包、备用安装与开发安装

PyPI 发行包名为 `hemispec-toolkit`；导入路径和 CLI 命令均为 `hemispec`：

```bash
python -m pip install hemispec-toolkit
hemispec --help
hemispec quickstart --out-dir hemispec_quickstart
```

GitHub Release 产物仍可作为离线、归档或 Windows 文件夹安装的备用来源：

```text
https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0
```

如需安装从 GitHub Releases 下载的本地 wheel：

```bash
python -m pip install hemispec_toolkit-0.1.0-py3-none-any.whl
hemispec --help
```

开发期间使用本地工具包检出：

```bash
cd <本地工具包检出目录>
python -m pip install -e .[gui,model,classifier]
hemispec --help
```

按需安装可选运行时额外依赖：

```bash
python -m pip install "hemispec-toolkit[gui]"         # 桌面启动器
python -m pip install "hemispec-toolkit[model]"       # PyTorch DGN 推理运行时
python -m pip install "hemispec-toolkit[classifier]"  # 保存的 sklearn/joblib 分类器验证
```

源码检出的开发额外依赖：

```bash
python -m pip install -e .[dev,gui]
```

公开文档应将软件称为 **HemiSpec Toolkit**，CLI 和 GUI 分别统一使用 `hemispec` 和 `hemispec-gui`。

## 神经影像前置条件

启用模型的工作流从预处理 GM 图开始，不能直接输入原始 T1。仓库研究脚本 `process_single_subject.sh` 与包内变体均依赖 BET、FAST、FLIRT 和 `fslmaths` 等 FSL 工具，将每张 T1 加权 NIfTI 转换为 MNI152 1.5 mm 空间的 `*_GM_masked.nii.gz`。

处理真实数据前，请阅读[输入与预处理](input-preprocessing.md)。该页明确脚本参数、`121 × 145 × 121` 已发布模型网格、`0.15` GM 阈值、质控项目与引用。

## GUI / 编译应用备用方案

推荐的 GUI 路径是在 PyPI 安装环境中运行 `hemispec-gui`。当前 GUI 是一个紧凑的标准工作流启动器，仅暴露正常 ANS/RNS 生成所需的用户决策：GM 输入 glob、输出工作区、可选 ROI atlas/标签表、可选分类器验证、可选 TRT 可靠性、运行控件和日志。

编译好的 Windows GUI 是一个 onedir 文件夹发行版，适用于无法方便管理 Python 环境时的备用/演示场景：

```text
dist/hemispec_gui/hemispec_gui.exe
```

请保持整个 `dist/hemispec_gui/` 文件夹完整；不要单独移动 `.exe` 文件。

## 模型运行时

DGN 推理需要在启动 CLI 或 GUI 的环境中安装 PyTorch，这也是 PyPI/conda 环境作为主要分发路径的原因。HemiSpec 从显式路径、环境变量、`assets/models/` 下的 Git-LFS 检出或每用户模型缓存中发现模型。Wheel/PyPI 和轻量 EXE 构建不嵌入 PyTorch 或 300MB+ 检查点；它们通过首次运行缓存下载使用已发布的 GitHub 资产。详见 [数据与模型](data-and-models.md)。
