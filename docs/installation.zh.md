# 安装

HemiSpec 有三个安装层：Python 包、CLI/GUI 入口点，以及编译好的桌面文件夹。

## 启用模型的安装

对于 PyPI/wheel 安装，安装运行时额外依赖，并可选择预先下载已发布的模型资产到用户缓存：

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

在 Windows 上，如果需要 GPU/CUDA 支持，请从已安装 PyTorch 的 conda 环境中运行上述命令。

## 工具包 / 发布包

HemiSpec v0.1.0 可从 GitHub Release 页面获取：

```text
https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0
```

下载 wheel 进行轻量 Python 安装：

```bash
python -m pip install hemispec_toolkit-0.1.0-py3-none-any.whl
hemispec --help
```

PyPI 发行包名为 `hemispec-toolkit`；导入路径和 CLI 命令均为 `hemispec`。开发期间使用本地工具包检出：

```bash
cd <本地工具包检出目录>
python -m pip install -e .[gui,model,classifier]
hemispec --help
```

需要桌面启动器时安装可选 GUI 依赖：

```bash
python -m pip install -e .[gui]
hemispec-gui
```

按需安装可选运行时额外依赖：

```bash
python -m pip install -e .[model]       # PyTorch DGN 推理运行时
python -m pip install -e .[classifier]  # 保存的 sklearn/joblib 分类器验证
python -m pip install -e .[dev,gui]     # 测试、构建工具、GUI 开发
```

公开文档应将软件称为 **HemiSpec Toolkit**，CLI 和 GUI 分别统一使用 `hemispec` 和 `hemispec-gui`。

## 神经影像前置条件

预处理工作流依赖 FSL 工具，如 BET、FAST、FLIRT 和 `fslmaths`。工具包的输入应为统一 MNI 空间网格中的灰质图，并根据工作流假设进行阈值处理和掩膜操作。

## GUI / 编译应用

当前 GUI 是一个紧凑的标准工作流启动器，仅暴露正常 ANS/RNS 生成所需的用户决策：GM 输入 glob、输出工作区、可选 ROI atlas/标签表、可选分类器验证、可选 TRT 可靠性、运行控件和日志。

编译好的 Windows GUI 是一个 onedir 文件夹发行版：

```text
dist/hemispec_gui/hemispec_gui.exe
```

请保持整个 `dist/hemispec_gui/` 文件夹完整；不要单独移动 `.exe` 文件。

## 模型运行时

DGN 推理需要在启动 CLI 或 GUI 的环境中安装 PyTorch。HemiSpec 从显式路径、环境变量、`assets/models/` 下的 Git-LFS 检出或每用户模型缓存中发现模型。Wheel/PyPI 和轻量 EXE 构建不嵌入 PyTorch 或 300MB+ 检查点；它们通过首次运行缓存下载使用已发布的 GitHub 资产。详见 [数据与模型](data-and-models.md)。
