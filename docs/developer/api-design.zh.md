# HemiSpec API 设计

本文档定义了半球重建结构特异性工具包的第一个稳定 Python API 层。

API 有意作为基础层。CLI、PyPI 打包和 GUI 部署应调用此层而非重复工作流逻辑。

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
examples/input_sample/
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

## 双向工作流 API

对于发布工作流，使用 `BilateralWorkflowConfig` 和 `run_bilateral_workflow`：

```python
from pathlib import Path
from hemispec import BilateralWorkflowConfig, run_bilateral_workflow

run = run_bilateral_workflow(
    BilateralWorkflowConfig(
        input_glob="/data/gm/*_GM_masked.nii.gz",
        out_dir=Path("/data/hemispec/full_workflow"),
        device="auto",
        run_classifier=False,
        run_trt=False,
    )
)

print(run.hemi_maps_dir)          # <输出目录>/voxel_maps
print(run.subject_summary_csv)    # <输出目录>/tables/subject_metric_summary.csv
print(run.roi_csv)                # 可选：启用 ROI atlas 导出时存在
print(run.roi_wide_csv)           # 可选：启用 ROI atlas 导出时存在
```

## CLI 和 GUI 规则

```text
CLI 参数 -> 配置数据类 -> API 函数
GUI 字段 -> 配置数据类 -> API 函数
```

新的工作流逻辑应首先添加到 API，然后通过 CLI 和 GUI 暴露。
