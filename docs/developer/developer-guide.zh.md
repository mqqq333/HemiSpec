# 开发指南

本指南描述 HemiSpec Toolkit 的工程布局。

## 仓库职责

HemiSpec Toolkit 有四个可分离的层：

1. **库包**（`src/hemispec/`）— 可导入的 Python 模块和公开 API。
2. **接口**（`hemispec` CLI 和 `hemispec-gui`）— 库包之上的薄层入口点。
3. **示例和测试**（`examples/`、`tests/`）— 合成或已批准的公开固件以及自动化回归检查。
4. **资产和发布包**（`assets/`、`dist/`）— 已批准的可复用模型包、仅供本地使用的 atlas，以及编译输出。

已批准的可复用 DGN/分类器包通过 Git LFS 位于 `assets/models/` 下。其他大型运行时资产应由清单记录并单独发布，除非已明确批准。

## 本地设置

```bash
python -m pip install -e .[dev]
python -m pytest
```

仅为需要的工作流安装可选额外依赖：

```bash
python -m pip install -e .[model]
python -m pip install -e .[classifier]
```

## 常用检查

```bash
python -m pytest
python -m build --wheel
python -m hemispec --help
hemispec --help
```

合成快速入门无需任何私有数据即可运行：

```powershell
powershell -ExecutionPolicy Bypass -File examples\synthetic_quickstart\run_synthetic_quickstart.ps1 -Python python
```

## 源码布局约定

- `api.py` 暴露稳定的程序化接口。
- `cli.py` 解析命令并委托给 API/工作流模块。
- `gui.py` 是桌面界面层；共享计算不应在此重复。
- `compute.py`、`similarity.py`、`roi.py`、`reports.py` 和 `plots.py` 包含专注的分析工具。
- `workflow.py` 协调多步骤双向工作流。
- `dgn_inference.py` 和 `dgn_model.py` 处理训练好的 DGN 推理。
- `hemisphere_classifier.py` 处理分类器验证工具。
- `paths.py` 集中管理本地资产发现。
- `resources/` 仅包含小型打包辅助脚本。

如果模块增长过大，按职责拆分而非按调用站点拆分。例如，GUI 特定 widget 可以移到 `hemispec/gui_app/`，CLI 子命令可以移到 `hemispec/commands/`。

## 数据和资产政策

不要提交真实受试者级 MRI/NIfTI 文件、生成输出或未批准的模型/atlas 有效载荷。`assets/models/` 下已批准的 HemiSpec DGN/分类器包是明确的例外，必须通过 Git LFS 追踪。对于其他资产，只提交：

- 描述预期放置位置的 README 文件。
- 带校验和和出处字段的清单模板。
- 安全可再发行的合成固件。

## 发布政策

PyPI wheel 应保持轻量，应包含包代码加上小型包自有资源。已发布的模型权重从 Git LFS 或首次运行用户缓存解析，不嵌入 wheel。编译应用文件夹可在 `dist/` 下生成，但额外发布资产在公开上传前需要明确批准。
