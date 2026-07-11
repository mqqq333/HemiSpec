# 安装

HemiSpec 采用软件包优先的结构，但当前 **PyPI 项目尚未公开**。v0.1.0 公开测试版目前通过 GitHub Release 和源码仓库分发。

## 推荐：通过源码检出运行模型工作流

运行 DGN 推理、GUI 或分类器验证时，推荐使用源码检出。Git LFS 会获取 `assets/models/` 下追踪的已发布模型包：

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e .[gui,model,classifier]
hemispec models --install --with-classifier  # 可选：预下载到缓存
hemispec-gui
```

PyTorch 必须安装在启动 HemiSpec 的同一 Python/conda 环境中。长时间模型运行前，应先配置合适的 CPU 或 CUDA PyTorch 版本。

## 安装 v0.1.0 Release wheel

从 GitHub Release 下载 `hemispec_toolkit-0.1.0-py3-none-any.whl`。运行基础 CLI 和合成快速测试：

```bash
python -m pip install ./hemispec_toolkit-0.1.0-py3-none-any.whl
hemispec --help
hemispec quickstart --out-dir hemispec_quickstart
```

从本地 wheel 请求可选依赖：

```bash
python -m pip install "./hemispec_toolkit-0.1.0-py3-none-any.whl[gui,model,classifier]"
```

如果本地 pip 不接受 wheel 路径后的 extras，可先安装 wheel，再显式安装所需可选依赖。

## 开发安装

```bash
python -m pip install -e .[dev,gui]
python -m pytest
python -m ruff check src tests
python -m mkdocs build --strict
```

软件包元数据中的发行名为 `hemispec-toolkit`，导入路径和 CLI 命令为 `hemispec`。未来发布到 PyPI 时应沿用该发行名，但在项目实际公开前，文档不能把它描述为可用安装源。

## 神经影像前置条件

启用模型的工作流从预处理 GM 图开始，不能直接输入原始 T1。仓库研究脚本 `process_single_subject.sh` 与包内变体均依赖 BET、FAST、FLIRT 和 `fslmaths` 等 FSL 工具，将每张 T1 加权 NIfTI 转换为 MNI152 1.5 mm 空间的 `*_GM_masked.nii.gz`。

处理真实数据前，请阅读[输入与预处理](input-preprocessing.md)。该页明确脚本参数、`121 × 145 × 121` 已发布模型网格、`0.15` GM 阈值、质控项目与引用。

## GUI 与编译备用产物

推荐从包含 PyTorch 的源码或本地 wheel 环境运行 `hemispec-gui`。GUI 暴露 GM 输入 glob、输出工作区、可选 ROI atlas/标签表、可选分类器验证、可选 TRT 可靠性、运行控制、日志和等效 CLI 命令。

GitHub Release v0.1.0 还归档了 Windows 备用产物。Onedir GUI 发行目录必须整体保留，不能只复制其中的可执行文件。

## 模型运行时

HemiSpec 从显式路径、环境变量、`assets/models/` 下的 Git-LFS 检出或每用户模型缓存中发现模型资产。Wheel 和轻量可执行程序不嵌入 PyTorch 或 300MB+ 模型包。启用自动下载时，缺失的已发布模型资产可从 GitHub Release 下载到缓存。详见[数据与模型](data-and-models.md)。
