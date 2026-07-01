# 发布产物

HemiSpec 以软件产物形式发布，而不仅仅是 GitHub 源码仓库。v0.1.0 的主要公开产物是 PyPI 上的 `hemispec-toolkit` Python 包，因为启用模型的使用最好放在 Python/PyTorch 环境中完成。GitHub Release 产物保留为归档、离线或 Windows 文件夹备用产物：[https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0](https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0)。

## v0.1.0 公开产物

```bash
python -m pip install hemispec-toolkit
```

```text
hemispec_toolkit-0.1.0-py3-none-any.whl          Python wheel
hemispec_toolkit-0.1.0.tar.gz                    源码发行版
HemiSpec-CLI-v0.1.0-win64.exe                    Windows CLI 可执行文件
HemiSpec-GUI-v0.1.0-win64.zip                    编译好的 GUI 文件夹发行版
HemiSpec-v0.1.0-SHA256SUMS.txt                   校验和
HemiSpec-v0.1.0-RELEASE_ARTIFACTS.txt            验证和产物清单
HemiSpec-Assets-<version>.zip                    用于非默认资产的可选离线/自定义资产包
```

同一公开 Python API 驱动 PyPI 安装的 CLI、PyPI 安装的 GUI 启动器以及任何编译备用应用，以确保示例和验证行为可复现。

ANS/RNS 指标使用应保持引用边界清晰：原始 ANS/RNS 和跨半球 DGN 框架来自 Wang 等人 2024 年 *Patterns* 论文；HemiSpec 为当前软件版本打包并扩展了该工作流。

## 构建命令

使用以下命令构建轻量包，以及（除非跳过）编译好的 Windows 产物：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_release.ps1 -Python "py -3.12"
```

可用开关：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_release.ps1 -Python "py -3.12" -SkipExe
powershell -ExecutionPolicy Bypass -File scripts\build_release.ps1 -Python "py -3.12" -SkipGuiSmoke
```

`-SkipGuiSmoke` 仅应在无头环境（无法进行 GUI 启动检查）中使用。

## 发布验收条件

发布只有在所有相关产物都构建并一起检查后才被视为公开就绪：

- `python -m build --wheel --sdist` 创建轻量 `hemispec-toolkit` 产物。
- `python -m twine check dist/hemispec_toolkit-*.whl dist/hemispec_toolkit-*.tar.gz` 在上传前验证包元数据。
- `python -m twine upload dist/hemispec_toolkit-*.whl dist/hemispec_toolkit-*.tar.gz` 将包发布到 PyPI。
- `pip install dist/*.whl` 或 `pip install hemispec-toolkit` 会在当前 Python/PyTorch 环境中暴露 `hemispec` 和 `hemispec-gui` 入口点。
- `hemispec quickstart --out-dir <tmpdir>` 在不需要源码检出的情况下运行内置公开安全合成冒烟测试。
- `hemispec --help` 和文档中的子命令在干净环境中运行。
- `hemispec-gui` 启动紧凑标准工作流 GUI。
- Windows 应用构建为文件夹发行版，仅包含已批准的运行时文件。
- 任何额外/离线 DGN 模型、atlas、分类器或示例数据包都有清单、校验和、许可证/出处说明和兼容版本。
- 公开产物和文档通过私有路径、密钥、受试者数据、模型有效载荷和未发表结果声明的泄露检查。

## 源码与资产

源码仓库包含代码、文档、测试、示例和通过 Git LFS 的已批准可复用模型包。Atlas NIfTI 文件、非公开神经影像衍生数据及任何额外/自定义模型包应单独发布，并附校验和、许可证和模型卡，除非已明确批准放入仓库。

## 桌面备用变体

- **轻量应用**：用于备用/演示场景的紧凑 GUI 加 CLI/API 工具；已发布模型从 Git LFS、缓存下载或用户配置路径解析。
- **启用模型的应用**：当 PyPI/conda 安装不方便时，将紧凑 GUI 加已批准的模型/atlas 资产和 PyTorch 运行时打包为较大文件夹发行版或与离线资产包配对。

两种变体都应在内部使用公开的 `hemispec` 包；对于能够管理 Python 环境的用户，它们不是首选路径。

## 发布后验证

v0.1.0 发布已于 2026-06-29 从 GitHub 重新下载。SHA256 校验和匹配，下载的 Windows CLI 打印了 `--help`，下载的 wheel 在全新本地验证工作区中运行了公开安全的合成快速入门。详见 [v0.1.0 发布验证](developer/release-verification-v0.1.0.md)。

## 相关页面

- [v0.1.0 发布验证](developer/release-verification-v0.1.0.md)
- [外部资产包](reference/asset-bundle.md)
- [路线图](developer/roadmap.md)
