# Python API

HemiSpec 更适合以 Python API 作为主入口来使用：PyTorch、模型缓存、批量运行和下游统计分析都可以放在同一个 Python/conda 环境中完成。PyPI 发行包名是 `hemispec-toolkit`，公开导入路径是 `hemispec`。

```bash
python -m pip install "hemispec-toolkit[model,classifier]"
```

```python
import hemispec
print(hemispec.__version__)
```

下面的 API 已按 HemiSpec v0.1.0 核对。新分析优先使用高层工作流 API；只有在需要手动拆分推理、指标计算或验证时，再使用底层 API。

本页覆盖的公开入口包括 `run_bilateral_workflow`、`ensure_default_dgn_models`、`ensure_default_classifier_models`、ROI 汇总辅助函数、`validate_specificity`、`validate_reliability`、`validate_hemisphere_classification`、底层 DGN/指标函数，以及合成快速测试入口。

## 推荐：一行式双向工作流

`run_bilateral_workflow()` 是主要 Python 入口。它会运行两个 DGN 方向、计算双侧 ANS/RNS 图，写出受试者级汇总，并可选导出 ROI 特征表、半球分类器验证和 test-retest reliability。

```python
from pathlib import Path

from hemispec import BilateralWorkflowConfig, run_bilateral_workflow

result = run_bilateral_workflow(
    BilateralWorkflowConfig(
        input_glob="derivatives/*_GM_masked.nii.gz",
        out_dir=Path("outputs/hemispec_workflow"),
        device="auto",          # "auto"、"cuda" 或 "cpu"
    )
)

print(result.out_dir)
print(result.hemi_maps_dir)          # 最终 ANS.L / ANS.R / RNS.L / RNS.R 图
print(result.subject_summary_csv)    # 每个受试者的体素均值汇总
```

当 atlas 可用时，ROI 导出默认开启。只有在只需要体素级图和受试者汇总、不需要 ROI 特征时，才设置 `export_roi_table=False`。

主要输出结构：

```text
outputs/hemispec_workflow/
  voxel_maps/<subject>_ANS.L.nii.gz
  voxel_maps/<subject>_ANS.R.nii.gz
  voxel_maps/<subject>_RNS.L.nii.gz
  voxel_maps/<subject>_RNS.R.nii.gz
  tables/subject_metric_summary.csv
```

## 在 Python 中管理模型资产

Wheel/PyPI 安装不会把大模型二进制文件打进 wheel。首次模型运行时，工作流会自动下载缺失的已发布 DGN 检查点，除非用户禁用了自动下载。也可以显式预下载：

```python
from hemispec import ensure_default_classifier_models, ensure_default_dgn_models

# 返回 DGN 模型根目录（.../models/dgn）。
dgn_root = ensure_default_dgn_models()

# 可选：半球分类器验证所需的模型包
classifier_dir = ensure_default_classifier_models(mode="single")
```

如果想显式指定模型路径，可以传入工作流配置：

```python
from pathlib import Path
from hemispec import BilateralWorkflowConfig, run_bilateral_workflow

result = run_bilateral_workflow(
    BilateralWorkflowConfig(
        input_glob="derivatives/*_GM_masked.nii.gz",
        out_dir=Path("outputs/hemispec_with_models"),
        model_root=dgn_root,
        run_classifier=True,
        classifier_model_dir=classifier_dir,
        roi_atlas=Path("atlas/custom_atlas.nii.gz"),
        roi_label_table=Path("atlas/custom_labels.xlsx"),
    )
)
```

常用环境变量：

```text
HEMISPEC_MODEL_CACHE              # 下载模型资产的用户缓存根目录
HEMISPEC_DGN_MODEL_ROOT           # 覆盖 DGN 检查点根目录
HEMISPEC_CLASSIFIER_MODEL_DIR     # 覆盖分类器模型包目录
HEMISPEC_GLASSER_ATLAS            # ROI 导出的默认 atlas 路径
HEMISPEC_GLASSER_LABEL_TABLE      # 默认标签表路径
HEMISPEC_DISABLE_MODEL_AUTO_DOWNLOAD=1
```

## 面向下游分析的 ROI 特征表

提供 atlas 后，可以生成用于统计模型或机器学习分类器的 ROI 水平特征。长表是每个受试者 / 图 / ROI 一行；宽表是每个受试者一行，特征列名类似 `ANS.L_roi_1` 或 `RNS.R_roi_180`。

```python
from pathlib import Path
from hemispec import BilateralWorkflowConfig, run_bilateral_workflow

result = run_bilateral_workflow(
    BilateralWorkflowConfig(
        input_glob="derivatives/*_GM_masked.nii.gz",
        out_dir=Path("outputs/hemispec_roi"),
        roi_atlas=Path("atlas/custom_atlas.nii.gz"),
        roi_label_table=Path("atlas/custom_labels.xlsx"),
        export_roi_table=True,
    )
)

print(result.roi_csv)       # tables/roi_features_bilateral.csv
print(result.roi_wide_csv)  # tables/roi_features_bilateral_wide.csv
```

如果已经有体素级图，也可以直接汇总到 ROI：

对于工作流生成的双侧图（如 `sub-001_ANS.L.nii.gz` 或 `sub-001_RNS.R.nii.gz`），请保留下面扩展的 `file_regex`，这样才能正确捕获 `map_hemi` 列。

```python
from pathlib import Path
from hemispec import RoiSummaryConfig, summarize_bilateral_roi_features, summarize_maps_by_atlas

roi_long = Path("outputs/tables/roi_features_bilateral.csv")
summary = summarize_maps_by_atlas(
    RoiSummaryConfig(
        maps_glob="outputs/hemispec_workflow/voxel_maps/*.nii.gz",
        atlas_path=Path("atlas/custom_atlas.nii.gz"),
        label_table=Path("atlas/custom_labels.xlsx"),
        out_csv=roi_long,
        file_regex=r"(?P<subject>.+?)_(?P<kind>ANS|RNS)[._](?P<map_hemi>L|R)\.nii(?:\.gz)?$",
    )
)
wide = summarize_bilateral_roi_features(roi_long, Path("outputs/tables/roi_features_bilateral_wide.csv"))
```

## 验证 API

如果需要在 Python 中控制输出目录或参数，可以直接调用验证 API。

```python
from pathlib import Path
from hemispec import HemisphereClassificationConfig, ValidationConfig
from hemispec import validate_hemisphere_classification, validate_reliability, validate_specificity

specificity = validate_specificity(
    ValidationConfig(
        maps_dir=Path("outputs/hemispec_workflow/intermediate/combined_maps"),
        out_dir=Path("outputs/validation/specificity"),
        hemis=("L", "R"),
        dgn_direction="bilateral",
    )
)
print(specificity.to_dataframe())

trt = validate_reliability(
    ValidationConfig(
        maps_dir=Path("outputs/hemispec_workflow/intermediate/combined_maps"),
        out_dir=Path("outputs/validation/trt"),
        file_regex=r"(sub-MSC\d+).*?(run-\d+)",
        session_a="run-01",
        session_b="run-02",
        dgn_direction="bilateral",
    )
)

classifier = validate_hemisphere_classification(
    HemisphereClassificationConfig(
        maps_dir=Path("outputs/hemispec_workflow/voxel_maps"),
        roi_csv=Path("outputs/hemispec_workflow/tables/roi_features_bilateral.csv"),
        atlas_path=Path("atlas/custom_atlas.nii.gz"),
        label_table=Path("atlas/custom_labels.xlsx"),
        out_dir=Path("outputs/validation/hemi_classify"),
    )
)
print(classifier.accuracy, classifier.predictions_csv)
```

## 底层推理和指标计算 API

只有在需要自定义管线布局、只跑单个 DGN 方向，或从已有重建图计算 ANS/RNS 时，才建议使用这些底层接口。

```python
from pathlib import Path
from hemispec import DGNInferenceConfig, MetricComputeConfig
from hemispec import compute_metrics, discover_local_dgn_bundles, run_dgn_inference

bundles = discover_local_dgn_bundles()
reconstructed = run_dgn_inference(
    DGNInferenceConfig(
        model=bundles["L_to_R"],
        input_glob="derivatives/*_GM_masked.nii.gz",
        out_dir=Path("outputs/recon_L_to_R"),
        device="auto",
        direction="L_to_R",
    )
)

metrics = compute_metrics(
    MetricComputeConfig(
        actual_glob="derivatives/*_GM_masked.nii.gz",
        reconstructed_glob="outputs/recon_L_to_R/*_PRED_LR_full.nii.gz",
        out_dir=Path("outputs/specificity_L_to_R"),
        save_subject_maps=True,
    )
)
print(metrics.subject_maps_dir)
```

## Python 合成冒烟测试

如果只是检查文档、CI 或环境连通性，不希望下载模型或接触私有 MRI 数据，可以运行合成快速测试：

```python
from pathlib import Path
from hemispec import run_synthetic_quickstart

run_synthetic_quickstart(Path("outputs/hemispec_quickstart"))
```

## 暂不作为稳定公开 API 的内容

训练代码、私有稿件分析和原始数据预处理决策不作为稳定公开 Python API 暴露。新增用户文档时，示例应使用 `from hemispec import ...`，并保证 CLI/GUI 示例与同一个包安装环境保持一致。
