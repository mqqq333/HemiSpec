# Python API

HemiSpec is designed to be used from Python first when you need reproducible PyTorch/model setup, batch execution, and downstream statistics in the same environment. The package distribution name is `hemispec-toolkit`; the public import path is `hemispec`. The PyPI project is not public yet.

Complete the [installation prerequisites](../installation.md) first. From the repository root, install the editable model and classifier extras:

```bash
python -m pip install -e ".[model,classifier]"
```

```python
import hemispec
print(hemispec.__version__)
```

The API below reflects the current `main` source checkout. A package version alone is insufficient to identify an editable checkout; record the exact source revision with `git rev-parse HEAD`. Prefer the high-level workflow API for new analyses; use lower-level APIs only when you need to split inference, metric computation, or validation manually.

Covered public entry points include `run_bilateral_workflow`, model discovery helpers, ROI summarization helpers, `validate_specificity`, `validate_reliability`, `validate_hemisphere_classification`, lower-level DGN/metric functions, and the synthetic quickstart helper.

## Recommended: one-call bilateral workflow

`run_bilateral_workflow()` is the main Python entry point. It runs both DGN directions, computes bilateral ANS/RNS maps, writes subject summaries, and optionally exports ROI feature tables, hemisphere-classifier validation, and test-retest reliability.

```python
from pathlib import Path

from hemispec import BilateralWorkflowConfig, run_bilateral_workflow

result = run_bilateral_workflow(
    BilateralWorkflowConfig(
        input_glob="derivatives/*_GM_masked.nii.gz",
        out_dir=Path("outputs/hemispec_workflow"),
        model_root=Path("assets/models/dgn"),
        device="auto",          # "auto", "cuda", or "cpu"
    )
)

print(result.out_dir)
print(result.hemi_maps_dir)          # final ANS.L / ANS.R / RNS.L / RNS.R maps
print(result.subject_summary_csv)    # per-subject voxel-wise means
```

ROI export is enabled by default when an atlas is available. Set `export_roi_table=False` only when you want voxel-wise maps and subject summaries without ROI features.

Before model inference, verify that every input matches the canonical FSL MNI152 1.5 mm grid, including shape, voxel size, orientation, and full affine; see [Input and preprocessing](../input-preprocessing.md).

Primary outputs are:

```text
outputs/hemispec_workflow/
  voxel_maps/<subject>_ANS.L.nii.gz
  voxel_maps/<subject>_ANS.R.nii.gz
  voxel_maps/<subject>_RNS.L.nii.gz
  voxel_maps/<subject>_RNS.R.nii.gz
  tables/subject_metric_summary.csv
```

## Model assets from Python

For the current source checkout, materialize the tracked model files with `git lfs pull` and use their local paths explicitly. Do not rely on classifier auto-download: the current `/media` endpoint returns HTTP 404 for `feature_names.csv`, so it does not provide a complete classifier bundle.

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

The atlas files are separately supplied local assets, not Git LFS files in the public source branch. The released classifier is compatible only with the MNI Glasser 1.5 mm mapping: labels `1..180` for the left hemisphere and `1001..1180` for the right hemisphere. Do not combine an arbitrary custom atlas with the released classifier.

Useful environment variables:

```text
HEMISPEC_MODEL_CACHE              # user cache root for downloaded model assets
HEMISPEC_DGN_MODEL_ROOT           # override DGN checkpoint root
HEMISPEC_CLASSIFIER_MODEL_DIR     # override classifier bundle directory
HEMISPEC_GLASSER_ATLAS            # default atlas path for ROI export
HEMISPEC_GLASSER_LABEL_TABLE      # default label table path
HEMISPEC_DISABLE_MODEL_AUTO_DOWNLOAD=1
```

## ROI feature tables for downstream analysis

Provide an atlas to create ROI-level features for downstream analysis. The long table stores one row per subject / map / ROI; the wide table stores one row per subject. A custom atlas is supported for ROI-only export, with `run_classifier=False`; its features are not inputs to the released Glasser classifier.

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

If you already have voxel-wise maps, summarize them directly:

For workflow-generated bilateral maps named like `sub-001_ANS.L.nii.gz` or `sub-001_RNS.R.nii.gz`, keep the extended `file_regex` below so the `map_hemi` column is captured correctly.

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

## Validation APIs

Use validation APIs when you want explicit Python control over output folders or parameters.

The examples below use two subjects scanned in both sessions:

```text
derivatives/sub-001_ses-01_GM_masked.nii.gz
derivatives/sub-001_ses-02_GM_masked.nii.gz
derivatives/sub-002_ses-01_GM_masked.nii.gz
derivatives/sub-002_ses-02_GM_masked.nii.gz
```

First run the bilateral workflow with retained intermediates. The default workflow removes `intermediate/` after successful completion.

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

Retained combined maps are named, for example, `sub-001_ses-01_ANS.nii.gz` and `sub-002_ses-02_RNS.nii.gz`. The regex captures `sub-001` as the subject and `ses-01` as the session. Use a fresh workflow and validation output directory for every alternate session pair or parameter variant.

## Lower-level inference and metric APIs

Use these only when you need a custom pipeline layout, a single DGN direction, or ANS/RNS computation from already reconstructed maps.

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

## Synthetic smoke test from Python

For documentation, CI, or environment checks that should not download model weights or touch private MRI data:

```python
from pathlib import Path
from hemispec import run_synthetic_quickstart

run_synthetic_quickstart(Path("outputs/hemispec_quickstart"))
```

## What is intentionally not public API

Training code, private manuscript analyses, and raw-data preprocessing decisions are not exposed as stable public Python API. For new user-facing work, document examples with `from hemispec import ...` and keep CLI/GUI examples aligned with the same package-installed environment.

ANS/RNS and the cross-hemispheric DGN framework originate from Wang et al. (2024); see [Citation](../citation.md).
