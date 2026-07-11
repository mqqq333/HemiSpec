# 快速开始

当前 v0.1.0 公开版本通过 GitHub Release 和源码检出提供，PyPI 项目尚未公开。

!!! note "命令命名"
    命令行界面使用 `hemispec`，图形界面使用 `hemispec-gui`。

## 1. 运行公开安全的合成测试

从 GitHub Release 下载 `hemispec_toolkit-0.1.0-py3-none-any.whl`，然后运行：

```bash
python -m pip install ./hemispec_toolkit-0.1.0-py3-none-any.whl
hemispec --help
hemispec quickstart --out-dir hemispec_quickstart
```

生成数据为合成数据，不是解剖学结果。该命令仅用于验证安装和公开文件/命令契约。

## 2. 安装启用模型的源码检出

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e .[gui,model,classifier]
hemispec models --install --with-classifier  # 可选：预下载到缓存
```

活动环境中必须安装 PyTorch。已发布 DGN 和分类器包可从 Git-LFS 检出读取，也可下载到用户缓存。

## 3. 准备 DGN 可用的灰质图

原始 T1 加权 MRI **不能**直接输入 `hemispec workflow`。在源码检出目录中运行研究使用的 FSL 预处理脚本：

```bash
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
  --out-dir outputs/hemispec_workflow
```

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

使用已批准的 atlas 和兼容标签表：

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_workflow \
  --roi-atlas /approved/path/atlas.nii.gz \
  --roi-label-table /approved/path/labels.xlsx
```

仅生成体素图：

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_workflow \
  --no-roi-table
```

## 7. 可选验证

半球分类和 TRT 均为可选步骤：

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_workflow \
  --run-classifier \
  --run-trt
```

分类器验证需要 ROI 特征；TRT 要求文件名符合配置的 session 模式。

如需后续运行独立验证命令，应保留中间文件：

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_workflow \
  --keep-intermediate

hemispec trt \
  --maps-dir outputs/hemispec_workflow/intermediate/combined_maps \
  --out-dir outputs/trt_validation
```

## 当前边界

- 没有独立 `report` 命令。
- 没有独立 `roi` 命令。
- 真实受试者 MRI、未发表队列结果和稿件草图不是公开示例。
- Atlas 文件需要记录来源和再分发批准。
- 行为表型教程仍是路线图页面，不是完整复现工作流。
