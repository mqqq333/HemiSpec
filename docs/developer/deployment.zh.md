# 部署

HemiSpec 可以部署为可安装的 Python 软件包、命令包装器、Windows CLI/GUI 构建，或启用模型的 Python 应用。当前公开的 v0.1.0 软件包产物通过 GitHub Releases 分发；PyPI 项目尚未公开。

## 1. Python 软件包

推荐用于分析服务器、集群和启用模型的运行：

```bash
cd <hemispec-checkout>
python -m pip install -e .[model]
hemispec --help
```

仅在需要时添加 GUI 或可选分类器依赖：

```bash
python -m pip install -e .[gui,model]
python -m pip install -e .[gui,model,classifier]
```

分类器始终是可选的下游验证分支。

已下载的 v0.1.0 wheel 可以直接安装：

```bash
python -m pip install ./hemispec_toolkit-0.1.0-py3-none-any.whl
```

## 2. Windows 命令包装器

安装软件包后，Windows 用户可以运行：

```bat
scripts\hemispec.cmd compute --help
```

该包装器委托给 `python -m hemispec %*`，不能包含另一套工作流逻辑。

## 3. Windows CLI 与 GUI 构建

安装开发和 GUI 依赖后构建：

```powershell
cd <hemispec-checkout>
python -m pip install -e .[dev,gui]
powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1
```

预期本地产物：

```text
dist/hemispec.exe
dist/hemispec_gui/hemispec_gui.exe
```

`hemispec_gui.exe` 是 onedir 构建。必须保留完整的 `dist/hemispec_gui/` 文件夹，不能只移动可执行文件。

干净构建环境示例：

```powershell
python -m venv .venv-build
.\.venv-build\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\.venv-build\Scripts\python.exe -m pip install -e .[dev,gui] --no-build-isolation
.\.venv-build\Scripts\python.exe -m PyInstaller --clean --onedir --windowed --name hemispec_gui scripts\hemispec_gui_entry.py
```

轻量 GUI 构建不嵌入 PyTorch、atlas 载荷、真实 MRI 数据或生成结果。

## 4. 启用模型的部署

启用模型的安装需要：

1. 包内 DGN 运行时代码；
2. `L_to_R` 与 `R_to_L` 两个方向的已批准生成器检查点；
3. 预处理与裁剪契约；
4. 合适的 PyTorch 环境；
5. 重建输出命名契约；
6. ANS/RNS 计算和可选验证设置。

模型资产布局见 [DGN 模型包](dgn-model-bundle.md)。资产可以来自 Git-LFS 源码检出、用户缓存、显式模型根目录或已批准的离线资产包。

```bash
hemispec models
hemispec infer \
  --direction L_to_R \
  --input-glob "<preprocessed-gm-dir>/*_GM_masked.nii.gz" \
  --out-dir "<hemispec-results>/recon_L_to_R" \
  --device cuda
```

标准双向工作流把 ROI 导出、分类器验证和 TRT 验证都作为可选参数；生成体素级 ANS/RNS 图不要求启用其中任何一项。

## 集群使用

Linux 集群使用 Python 软件包形式：

```bash
module load python
cd <remote-hemispec-checkout>
python -m pip install -e .[model]
hemispec workflow \
  --input-glob "<preprocessed-gm-dir>/*_GM_masked.nii.gz" \
  --out-dir "<hemispec-results>/bilateral" \
  --device cuda
```

单方向推理并计算指标：

```bash
hemispec run \
  --direction L_to_R \
  --input-glob "<preprocessed-gm-dir>/*_GM_masked.nii.gz" \
  --recon-dir "<hemispec-results>/recon_L_to_R" \
  --metrics-dir "<hemispec-results>/ANS_RNS_thr0p15" \
  --device cuda
```

公开/私有资产边界见[数据与模型](../data-and-models.md)和[发布产物](../release-artifacts.md)。
