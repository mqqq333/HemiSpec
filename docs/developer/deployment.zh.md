# 部署

本项目可以四种实际形式部署：PyPI 包、CLI 包装器、GUI/EXE 构建和启用模型的编译应用。

## 1. Python 包

适用于分析服务器和集群。

```bash
cd <hemispec-toolkit-checkout>
python -m pip install -e .
hemispec --help
```

固定安装：

```bash
python -m pip install .
```

训练好的 DGN 推理：

```bash
python -m pip install .[model]
```

## 2. CMD 包装器

安装包后，Windows 用户可以运行：

```bat
scripts\hemispec.cmd compute --help
```

该包装器简单调用：

```bat
python -m hemispec %*
```

## 3. EXE / 编译 GUI 构建

安装 PyInstaller 并构建：

```powershell
cd <hemispec-toolkit-checkout>
python -m pip install -e .[dev]
powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1
```

命令行可执行文件应出现在：

```text
dist/hemispec.exe
```

图形可执行文件应出现在：

```text
dist/hemispec_gui/hemispec_gui.exe
```

重要：`hemispec_gui.exe` 是 onedir 构建。请保持整个 `dist/hemispec_gui/` 文件夹完整；不要单独移动 `.exe`。

Windows 干净构建示例：

```powershell
python -m venv .venv-build
.\.venv-build\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\.venv-build\Scripts\python.exe -m pip install -e .[dev] --no-build-isolation
.\.venv-build\Scripts\python.exe -m PyInstaller --clean --onedir --windowed --name hemispec_gui scripts\hemispec_gui_entry.py
```

当前轻量 GUI EXE 不打包 PyTorch。它可以打开紧凑标准工作流 GUI，但启用模型的 DGN 推理需要 PyTorch 环境以及来自 Git LFS、首次运行缓存下载、显式模型根或单独模型启用/Torch 包的已发布 DGN 资产。

## 4. 启用模型的部署

当前 Python 包/CLI 包含训练好的 DGN 推理入口点以及已发布模型默认值的首次运行下载。当前 GUI 有意只暴露带可选 ROI、分类器和 TRT 分支的标准 ANS/RNS 工作流；底层推理、计算、特异性和分类器命令仍可通过 CLI/API 使用。

启用模型的发布应包含或加载：

```text
1. 包自有 DGN 运行时代码
2. 训练好的模型检查点/权重
3. 预处理/裁剪规则
4. 推理命令和紧凑 GUI 标准工作流
5. 重建 GM 输出命名约定
6. ANS/RNS 计算和验证流水线
```

## 集群使用

在 Linux 集群上使用 Python 包形式。SLURM 示例：

```bash
module load python
cd <remote-hemispec-toolkit>
python -m pip install -e .
hemispec compute \
  --actual-glob "<preprocessed-gm-dir>/*.nii.gz" \
  --predicted-glob "<reconstruction-dir>/*_PRED_LR_full.nii.gz" \
  --out-dir "<hemispec-results>/ANS_RNS_thr0p15" \
  --gm-thresh 0.15 \
  --save-subject-maps
```

端到端 DGN 推理加 ANS/RNS 计算：

```bash
hemispec run \
  --direction L_to_R \
  --input-glob "<preprocessed-gm-dir>/*_GM_masked.nii.gz" \
  --recon-dir "<hemispec-results>/recon_L_to_R" \
  --metrics-dir "<hemispec-results>/ANS_RNS_thr0p15" \
  --device cuda
```
