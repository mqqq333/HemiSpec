# HemiSpec API 设计

本文档定义了半球重建结构特异性工具包的第一个稳定 Python API 层。

API 有意作为基础层。CLI、软件包分发和 GUI 部署应调用此层而非重复工作流逻辑。

## 公开包名

保持当前导入名以确保兼容性：

```python
import hemispec
```

产品名可以呈现为 `HemiSpec`，而包在发布命名确定前保持为 `hemispec-toolkit` / `hemispec`。

## 工作流顺序

目标产品工作流为：

```text
预处理 GM -> DGN 推理 -> 重建 GM -> ANS/RNS -> 可靠性/特异性验证
```

预处理契约记录于：

```python
from hemispec import get_preprocessing_spec

spec = get_preprocessing_spec()
print(spec.script_path)
print(spec.sample_input_dir)
```

预期预处理脚本为：

```text
src/hemispec/resources/preprocess/process_single_subject_GM_v2_reorient.sh
```

它产生 `*_GM_masked.nii.gz` 文件。示例输入在：

```text
examples/synthetic_quickstart/
```

## 指标 API

使用 `MetricComputeConfig` 和 `compute_metrics` 计算 ANS/RNS 图：

```python
from pathlib import Path
from hemispec import MetricComputeConfig, compute_metrics

result = compute_metrics(
    MetricComputeConfig(
        actual_glob="/data/gm/*_GM_masked.nii.gz",
        reconstructed_glob="/data/recon/*_PRED_LR_full.nii.gz",
        out_dir=Path("/data/hemispec/metrics"),
        gm_thresh=0.15,
        save_subject_maps=True,
    )
)

print(result.n_pairs)
print(result.out_dir)
```

输出：

```text
ANS_group_masked_mean.nii.gz
RNS_group_masked_mean.nii.gz
validN.nii.gz
coverage.nii.gz
subject_maps/<subject>_ANS.nii.gz
subject_maps/<subject>_RNS.nii.gz
```

## 验证 API

使用 `ValidationConfig` 和 `validate_specificity` 或 `validate_reliability`：

```python
from pathlib import Path
from hemispec import ValidationConfig, validate_specificity

run = validate_specificity(
    ValidationConfig(
        maps_dir=Path("/data/hemispec/metrics/subject_maps"),
        out_dir=Path("/data/hemispec/specificity"),
        hemis=("L", "R"),
        session_a="run-01",
        session_b="run-02",
        write_plots=True,
    )
)

df = run.to_dataframe()
```

两个函数使用相同的矩阵引擎：

```text
组内相似度   = 对角线扫描 A 与扫描 B 相似度
组间相似度   = 非对角线相似度
特异性指数   = mean(组内) - mean(组间)
Top-1 匹配率 = 最佳匹配为同一受试者的行的百分比
```

当输入为重复扫描时，`validate_reliability` 是同一计算的解释别名。

## DGN 推理 API

公开契约已定义：

```python
from pathlib import Path
from hemispec import (
    DGNInferenceConfig,
    discover_local_dgn_bundles,
    run_dgn_inference,
)

bundles = discover_local_dgn_bundles()
config = DGNInferenceConfig(
    model=bundles["L_to_R"],
    input_glob="/data/gm/*_GM_masked.nii.gz",
    out_dir=Path("/data/recon"),
    device="cuda",
)

run_dgn_inference(config)
```

对于常见的端到端工作流，使用 `PipelineRunConfig` 和 `run_pipeline`：

```python
from pathlib import Path
from hemispec import PipelineRunConfig, run_pipeline

run = run_pipeline(
    PipelineRunConfig(
        inference=config,
        metrics_out_dir=Path("/data/hemispec/ANS_RNS_thr0p15"),
        save_subject_maps=True,
    )
)

print(run.reconstructed_paths)
print(run.metrics.subject_maps_dir)
```

DGN 本地模型包发现遵循已确认的产品级映射：

```text
outputs_bi_stable_L = R_to_L = 右半球 -> 生成左半球
outputs_bi_stable_R = L_to_R = 左半球 -> 生成右半球
```

检查 checkpoint 位置、裁剪约定和当前 adapter 状态，请参阅 [DGN 模型包](dgn-model-bundle.md)。

API 现已为经过训练的 PyTorch Generator checkpoint 提供包内运行时 adapter。执行真实 DGN 推理前，请安装 `model` extra：

```bash
python -m pip install -e ".[model]"
```

`train_code/` 仅供参考。运行时推理使用包内模块和训练好的 checkpoint，而非训练脚本。公开模型包契约面向部署推理资产，不暴露训练代码路径。

## 双向工作流 API

发布工作流使用 `BilateralWorkflowConfig` 和 `run_bilateral_workflow`。这是精简 GUI 标准工作流和 CLI `hemispec workflow` 命令背后的 API 入口。

```python
from pathlib import Path
from hemispec import BilateralWorkflowConfig, run_bilateral_workflow

run = run_bilateral_workflow(
    BilateralWorkflowConfig(
        input_glob="/data/gm/*_GM_masked.nii.gz",
        out_dir=Path("/data/hemispec/full_workflow"),
        device="auto",
        run_classifier=False,  # opt in only when ROI table/classifier validation is needed
        run_trt=False,
    )
)

print(run.hemi_maps_dir)          # <out-dir>/voxel_maps
print(run.subject_summary_csv)    # <out-dir>/tables/subject_metric_summary.csv
print(run.roi_csv)                # optional: present when ROI atlas export is enabled and available
print(run.roi_wide_csv)           # optional: present when ROI atlas export is enabled and available
print(run.combined_maps_dir)      # intermediate path; removed unless keep_intermediate=True
```

该工作流运行两个已部署的 DGN 推理方向：

```text
L_to_R = 左半球 -> 生成右半球
R_to_L = 右半球 -> 生成左半球
```

最终面向用户的 voxel map 直接以按半球区分的 ANS/RNS map 写入：

```text
voxel_maps/<subject>_ANS.L.nii.gz
voxel_maps/<subject>_ANS.R.nii.gz
voxel_maps/<subject>_RNS.L.nii.gz
voxel_maps/<subject>_RNS.R.nii.gz
```

只有启用 `keep_intermediate=True` / `--keep-intermediate` 时，DGN 重建结果、单方向指标和合并后的双侧 map 才会保存在 `intermediate/` 下。

启用 ROI atlas 导出且 atlas 可用时，ROI 输出包括供已保存分类器 adapter 使用的长表，以及便于下游直接使用的宽表。未提供 atlas 时，voxel-wise ANS/RNS map 仍是主要输出；用户也可通过自己的下游方法提取 ROI 特征：

```text
tables/roi_features_bilateral.csv
tables/roi_features_bilateral_wide.csv
```

宽表每位受试者占一行，特征名明确标记指标和半球，例如：

```text
ANS.L_roi_1
ANS.R_roi_1
RNS.L_roi_1
RNS.R_roi_1
```

受试者汇总表报告各半球均值，以及基于有限值 voxel 的 ANS/RNS 全脑均值：

```text
ANS.L_mean
ANS.R_mean
RNS.L_mean
RNS.R_mean
ANS.whole_brain_mean
RNS.whole_brain_mean
```

## CLI 和 GUI 规则

```text
CLI 参数 -> 配置数据类 -> API 函数
GUI 字段 -> 配置数据类 -> API 函数
```

CLI 的 `models`、`infer`、`run`、`workflow`、`compute`、`trt`、`specificity` 和 `hemi-classify` 子命令遵循此规则。

精简 GUI 通过单一标准工作流界面遵循相同规则：

```text
输入 GM 图 -> 输出工作区 -> 可选 ROI 表 -> 可选验证 -> 运行 HemiSpec
```

GUI 仅呈现普通用户需要决策的选项。模型根目录、设备、阈值、后缀规则、分类器包路径和 TRT 正则表达式均封装在文档化默认值中；高级用户也可通过 CLI/API 使用这些选项。新的工作流逻辑应先加入 API，再通过 CLI 和 GUI 暴露。
