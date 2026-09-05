# 快速开始

以下命令对应当前 `main` 分支源码，不适用于归档 `v0.1.0` wheel 的全部功能。PyPI 项目尚未公开。发行版本边界见[安装](installation.md)。

!!! note "命令命名"
    命令行界面使用 `hemispec`，图形界面使用 `hemispec-gui`。

## 1. 安装当前源码

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e ".[gui,model,classifier]"
git rev-parse HEAD
hemispec models
hemispec --help
```

活动环境中必须安装 PyTorch。运行记录中应保留 Git commit。`git lfs pull` 必须取得实际的 DGN 和分类器文件。分类器使用这些本地模型包；当前分类器缓存下载存在 CSV 地址问题，详见[数据与模型](data-and-models.md)。

## 2. 运行合成测试

在已安装的源码目录中运行：

```bash
hemispec quickstart --out-dir hemispec_quickstart
```

生成数据为合成数据，不是解剖学结果。该测试不执行模型推理，只检查安装和文件/命令契约。使用新的或空的输出目录；当前 `--force` 会删除整个指定目录，包括无关文件。

## 3. 准备 DGN 可用的灰质图

原始 T1 加权 MRI **不能**直接输入 `hemispec workflow`。在源码检出目录中运行研究使用的 FSL 预处理脚本：

```bash
mkdir -p derivatives
bash process_single_subject.sh \
  raw/sub-001_T1w.nii.gz \
  derivatives/sub-001
```

预期 DGN 输入：

```text
derivatives/sub-001_GM_masked.nii.gz
```

推理前应检查 `121 × 145 × 121` 网格、`1.5 mm` 体素大小、affine、有限的 `0–1` GM 数值、配准、分割和掩膜质量。详见[输入与预处理](input-preprocessing.md)。

## 4. 运行标准双向工作流

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_workflow \
  --no-roi-table
```

首次运行生成体素图和受试者汇总，不需要 atlas。每次运行，包括重试或更换输入子集，都使用新的输出目录，避免混合本次与既往输出。

主要输出：

```text
outputs/hemispec_workflow/
├── voxel_maps/     # 每名受试者的 ANS.L、ANS.R、RNS.L、RNS.R
├── tables/         # 受试者汇总和可选 ROI 表
└── validation/     # 可选分类器/TRT 输出
```

ANS/RNS 与跨半球 DGN 框架源自 Wang 等人（2024），详见[ANS 与 RNS 指标](methods/ans-rns-metrics.md)。

## 5. 启动 GUI

```bash
hemispec-gui
```

GUI 会报告 PyTorch、DGN、atlas 和分类器的就绪状态。用户选择 GM 输入 glob、输出工作区、可选 ROI 导出、可选半球分类器验证、可选 TRT 可靠性，以及是否保留中间文件。详见[GUI 用户指南](developer/gui-user-guide.md)。

## 6. 可选 ROI 表

使用与 GM 图网格一致、来源已批准的 atlas 和兼容标签表。自定义 atlas 可用于 ROI 汇总，但不能替代已发布分类器训练时使用的 atlas：

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_roi \
  --roi-atlas /approved/path/atlas.nii.gz \
  --roi-label-table /approved/path/labels.xlsx
```

## 7. 可选验证

### 半球分类

已发布分类器要求兼容的 Glasser atlas：每侧 180 个同源脑区，左侧标签为 `1–180`，右侧为 `1001–1180`，且位于相同的 1.5 mm 网格。公开仓库不分发该 atlas，应按照[数据与模型](data-and-models.md)准备 atlas 和标签表。仅有相同标签编号不能证明解剖学兼容。

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_classifier \
  --roi-atlas /approved/path/glasser_1p5mm.nii.gz \
  --roi-label-table /approved/path/glasser_labels.csv \
  --classifier-model-dir assets/models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models \
  --run-classifier
```

### 重测可靠性

TRT 要求至少两名受试者，每人有两次扫描。例如，另行准备以下输入目录：

```text
derivatives_trt/
  sub-001_run-01_GM_masked.nii.gz
  sub-001_run-02_GM_masked.nii.gz
  sub-002_run-01_GM_masked.nii.gz
  sub-002_run-02_GM_masked.nii.gz
```

为这些文件名显式指定受试者/session 模式。保留中间文件后，也可在后续单独运行验证：

```bash
hemispec workflow \
  --input-glob "derivatives_trt/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_trt \
  --no-roi-table \
  --keep-intermediate \
  --run-trt \
  --trt-file-regex '(?P<subject>sub-[0-9]+)_(?P<session>run-[0-9]+)' \
  --trt-session-a run-01 \
  --trt-session-b run-02

hemispec trt \
  --maps-dir outputs/hemispec_trt/intermediate/combined_maps \
  --out-dir outputs/trt_validation \
  --file-regex '(?P<subject>sub-[0-9]+)_(?P<session>run-[0-9]+)' \
  --session-a run-01 \
  --session-b run-02
```

## 当前边界

- 没有独立 `report` 命令。
- 没有独立 `roi` 命令。
- 真实受试者 MRI、未发表队列结果和稿件草图不是公开示例。
- Atlas 文件需要记录来源和再分发批准。
- 行为表型教程仍是路线图页面，不是完整复现工作流。
