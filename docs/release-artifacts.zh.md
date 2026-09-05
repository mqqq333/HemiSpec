# 发布产物

本页区分归档的 `v0.1.0` GitHub Release 与当前 `main` 源码树。两者当前都显示软件包版本 `0.1.0`，但功能集并不相同。`hemispec-toolkit` 项目**当前尚未在 PyPI 公开**。

## 归档的 v0.1.0 产物

v0.1.0 GitHub Release 提供：

```text
hemispec_toolkit-0.1.0-py3-none-any.whl          Python wheel
hemispec_toolkit-0.1.0.tar.gz                    源码发行包
HemiSpec-CLI-v0.1.0-win64.exe                    Windows CLI 可执行文件
HemiSpec-GUI-v0.1.0-win64.zip                    Windows GUI 文件夹发行版
HemiSpec-v0.1.0-SHA256SUMS.txt                   校验和
HemiSpec-v0.1.0-RELEASE_ARTIFACTS.txt            发布清单
```

从 [v0.1.0 GitHub Release](https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0) 下载所需产物。安装已下载的 wheel：

```bash
python -m pip install ./hemispec_toolkit-0.1.0-py3-none-any.whl
hemispec --help
```

归档 `v0.1.0` 标签不包含当前的合成快速入门或 `model_assets` 下载器。当前文档和启用模型的工作流应使用当前源码检出：

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e ".[gui,model,classifier]"
git rev-parse HEAD
```

每次分析都应记录提交哈希，因为仅凭软件包版本无法区分当前源码与归档标签。请使用 Git-LFS 检出中的分类器资产，或显式配置本地目录。

## 科学归因

跨半球 DGN 框架与两种 specificity 指标源自 Wang 等人（2024）：**ANS** 为 **absolute neuroanatomical specificity（绝对神经解剖特异性）**，**RNS** 为 **relative neuroanatomical specificity（相对神经解剖特异性）**。原始论文与软件发布应分别引用，详见[引用](citation.md)。

## 构建命令

维护者可以使用以下命令构建软件包与 Windows 产物：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_release.ps1 -Python "py -3.12"
```

可用变体：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_release.ps1 -Python "py -3.12" -SkipExe
powershell -ExecutionPolicy Bypass -File scripts\build_release.ps1 -Python "py -3.12" -SkipGuiSmoke
```

`-SkipGuiSmoke` 只应用于无法执行 GUI 启动检查的无图形环境。

## 发布验收检查

公开发布前：

- 使用 `python -m build --wheel --sdist` 构建 wheel 和源码发行包；
- 使用 `python -m twine check dist/hemispec_toolkit-*.whl dist/hemispec_toolkit-*.tar.gz` 验证元数据；
- 本地安装构建出的 wheel，并运行 `hemispec quickstart --out-dir <tmpdir>`；
- 在干净环境检查 `hemispec --help`、`hemispec-gui` 和文档中的子命令；
- 核对校验和与发布清单；
- 确认没有私有路径、凭据、受试者数据、未批准的模型/atlas 载荷或未发表结果声明。

上传 PyPI 是未来单独的发布动作。只有当项目在 PyPI 实际公开后，文档才能把 PyPI 安装写成当前可用方式。

## 源码与资产边界

当前源码仓库包含代码、文档、测试、合成示例，以及通过 Git LFS 跟踪的已批准可复用模型包。不能把这些当前源码功能归于归档 `v0.1.0` 软件包。Atlas 载荷、真实神经影像数据、生成结果和额外自定义模型包必须保留在公开源码树之外，除非已经记录其出处、许可证、再分发批准、校验和与兼容版本。

轻量 Windows CLI/GUI 产物不嵌入 PyTorch、atlas 载荷、真实 MRI 输入或生成结果。启用模型的工作流需要合适的 Python/PyTorch 环境，并从 Git-LFS 源码检出、用户缓存或离线资产包获得已批准模型。

## 发布后验证

v0.1.0 产物于 2026 年 6 月 29 日在发布后重新下载并检查：记录的校验和一致，Windows CLI 能显示 `--help`，wheel 可从干净环境导入。没有保留证据证明下载的 wheel 运行过后来加入的合成快速入门。详见 [v0.1.0 发布验证](developer/release-verification-v0.1.0.md)。

## 相关页面

- [安装](installation.md)
- [数据与模型](data-and-models.md)
- [外部资产包](reference/asset-bundle.md)
- [路线图](developer/roadmap.md)
