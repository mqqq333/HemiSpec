# Python API

HemiSpec 更适合以 Python API 作为主入口来使用：PyTorch、模型缓存、批量运行和下游统计分析都可以放在同一个 Python/conda 环境中完成。软件包发行名是 `hemispec-toolkit`，公开导入路径是 `hemispec`；当前 PyPI 项目尚未公开。

请先完成[安装前提条件](../installation.zh.md)。然后在仓库根目录安装可编辑模式下的 model 和 classifier 额外依赖：

```bash
python -m pip install -e ".[model,classifier]"
```

```python
import hemispec
print(hemispec.__version__)
```

下面的 API 反映当前 `main` 源码检出。仅记录软件包版本不足以标识可编辑源码检出；请使用 `git rev-parse HEAD` 记录准确源码修订。新分析优先使用高层工作流 API；只有在需要手动拆分推理、指标计算或验证时，再使用底层 API。

本页覆盖的公开入口包括 `run_bilateral_workflow`、模型发现辅助函数、ROI 汇总辅助函数、`validate_specificity`、`validate_reliability`、`validate_hemisphere_classification`、底层 DGN/指标函数，以及合成快速测试入口。

## 推荐：一行式双向工作流

`run_bilateral_workflow()` 是主要 Python 入口。它会运行两个 DGN 方向、计算双侧 ANS/RNS 图，写出受试者级汇总，并可选导出 ROI 特征表、半球分类器验证和 test-retest reliability。

```python
from pathlib import Path

from hemispec import BilateralWorkflowConfig, run_bilateral_workflow

result = run_bilateral_workflow(
    BilateralWorkflowConfig(
        input_glob="derivatives/*_GM_masked.nii.gz",
        out_dir=Path("outputs/hemispec_workflow"),
        model_root=Path("assets/models/dgn"),
        device="auto",          # "auto"、"cuda" 或 "cpu"
    )
)

print(result.out_dir)
print(result.hemi_maps_dir)          # 最终 ANS.L / ANS.R / RNS.L / RNS.R 图
print(result.subject_summary_csv)    # 每个受试者的体素均值汇总
```

当 atlas 可用时，ROI 导出默认开启。只有在只需要体素级图和受试者汇总、不需要 ROI 特征时，才设置 `export_roi_table=False`。

模型推理前必须确认每个输入均匹配标准 FSL MNI152 1.5 mm 网格，包括形状、体素大小、方向和完整 affine；详见[输入与预处理](../input-preprocessing.zh.md)。

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

对于当前源码检出，请先运行 `git lfs pull` 取得受 Git LFS 管理的模型文件，再显式使用本地路径。不要依赖分类器自动下载：当前 `/media` 端点请求 `feature_names.csv` 时返回 HTTP 404，因此无法提供完整分类器包。

```python
from pathlib import Path
from hemispec import BilateralWorkflowConfig, run_bilateral_workflow

dgn_root = Path("assets/models/dgn")
classifier_dir = Path(
    "assets/models/hemisphere_classifier/"
    "OUT_noICBM_train_ICBM_external_saved_models"
)
glasser_atlas = Path(
    "assets/atlases/glasser/MNI_Glasser_HCP_v1.0_1p5mm.nii.gz"
)
glasser_labels = Path(
    "assets/atlases/glasser/Glasser_label_index_mapping.xlsx"
)

result = run_bilateral_workflow(
    BilateralWorkflowConfig(
        input_glob="derivatives/*_GM_masked.nii.gz",
        out_dir=Path("outputs/hemispec_with_models"),
        model_root=dgn_root,
        run_classifier=True,
        classifier_model_dir=classifier_dir,
        roi_atlas=glasser_atlas,
        roi_label_table=glasser_labels,
    )
)
```

atlas 文件是另外提供的本地资产，不属于公开源码分支中的 Git LFS 文件。已发布分类器只兼容 MNI Glasser 1.5 mm 标签映射：左半球为 `1..180`，右半球为 `1001..1180`。不要将任意自定义 atlas 与已发布分类器组合使用。

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

提供 atlas 后，可以生成用于下游分析的 ROI 水平特征。长表是每个受试者 / 图 / ROI 一行；宽表是每个受试者一行。自定义 atlas 只支持 ROI 导出，并应设置 `run_classifier=False`；其特征不能作为已发布 Glasser 分类器的输入。

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
        run_classifier=False,
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

如果需要在 Python 中控制输出目录或参数，可以直接调用验证 API。下面使用两个受试者、每个受试者两个重复扫描 session：

```text
derivatives/sub-001_ses-01_GM_masked.nii.gz
derivatives/sub-001_ses-02_GM_masked.nii.gz
derivatives/sub-002_ses-01_GM_masked.nii.gz
derivatives/sub-002_ses-02_GM_masked.nii.gz
```

先运行双向工作流并保留中间结果；默认工作流会在成功后删除 `intermediate/`。

```python
from pathlib import Path
from hemispec import BilateralWorkflowConfig, HemisphereClassificationConfig, ValidationConfig
from hemispec import run_bilateral_workflow
from hemispec import validate_hemisphere_classification, validate_reliability, validate_specificity

workflow = run_bilateral_workflow(
    BilateralWorkflowConfig(
        input_glob="derivatives/sub-*_ses-*_GM_masked.nii.gz",
        out_dir=Path("outputs/hemispec_trt_ses01_ses02"),
        model_root=Path("assets/models/dgn"),
        roi_atlas=Path("assets/atlases/glasser/MNI_Glasser_HCP_v1.0_1p5mm.nii.gz"),
        roi_label_table=Path("assets/atlases/glasser/Glasser_label_index_mapping.xlsx"),
        keep_intermediate=True,
    )
)

specificity = validate_specificity(
    ValidationConfig(
        maps_dir=workflow.combined_maps_dir,
        out_dir=Path("outputs/validation/specificity_ses01_ses02"),
        file_regex=r"(?P<subject>sub-[^_]+)_(?P<session>ses-[^_]+)_",
        session_a="ses-01",
        session_b="ses-02",
        hemis=("L", "R"),
        dgn_direction="bilateral",
    )
)
print(specificity.to_dataframe())

trt = validate_reliability(
    ValidationConfig(
        maps_dir=workflow.combined_maps_dir,
        out_dir=Path("outputs/validation/trt_ses01_ses02"),
        file_regex=r"(?P<subject>sub-[^_]+)_(?P<session>ses-[^_]+)_",
        session_a="ses-01",
        session_b="ses-02",
        dgn_direction="bilateral",
    )
)

classifier = validate_hemisphere_classification(
    HemisphereClassificationConfig(
        maps_dir=workflow.hemi_maps_dir,
        roi_csv=workflow.roi_csv,
        classifier_model_dir=Path(
            "assets/models/hemisphere_classifier/"
            "OUT_noICBM_train_ICBM_external_saved_models"
        ),
        out_dir=Path("outputs/validation/hemi_classify_ses01_ses02"),
    )
)
print(classifier.accuracy, classifier.predictions_csv)
```

保留的双侧合并图文件名示例为 `sub-001_ses-01_ANS.nii.gz` 和 `sub-002_ses-02_RNS.nii.gz`。该正则表达式会把 `sub-001` 捕获为受试者，把 `ses-01` 捕获为 session。每个替代 session 配对或参数变体都应使用新的工作流和验证输出目录。

## 底层推理和指标计算 API

只有在需要自定义管线布局、只跑单个 DGN 方向，或从已有重建图计算 ANS/RNS 时，才建议使用这些底层接口。

```python
from pathlib import Path
from hemispec import DGNInferenceConfig, MetricComputeConfig
from hemispec import compute_metrics, discover_local_dgn_bundles, run_dgn_inference

bundles = discover_local_dgn_bundles(Path("assets/models/dgn"))
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

ANS/RNS 与跨半球 DGN 框架源自 Wang 等人（2024），详见[引用](../citation.md)。
