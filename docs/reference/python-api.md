# Python API

HemiSpec is designed to be used from Python first when you need reproducible PyTorch/model setup, batch execution, and downstream statistics in the same environment. The PyPI distribution name is `hemispec-toolkit`; the public import path is `hemispec`.

```bash
python -m pip install "hemispec-toolkit[model,classifier]"
```

```python
import hemispec
print(hemispec.__version__)
```

The API below was checked against HemiSpec v0.1.0. Prefer the high-level workflow API for new analyses; use lower-level APIs only when you need to split inference, metric computation, or validation manually.

Covered public entry points include `run_bilateral_workflow`, `ensure_default_dgn_models`, `ensure_default_classifier_models`, ROI summarization helpers, `validate_specificity`, `validate_reliability`, `validate_hemisphere_classification`, lower-level DGN/metric functions, and the synthetic quickstart helper.

## Recommended: one-call bilateral workflow

`run_bilateral_workflow()` is the main Python entry point. It runs both DGN directions, computes bilateral ANS/RNS maps, writes subject summaries, and optionally exports ROI feature tables, hemisphere-classifier validation, and test-retest reliability.

```python
from pathlib import Path

from hemispec import BilateralWorkflowConfig, run_bilateral_workflow

result = run_bilateral_workflow(
    BilateralWorkflowConfig(
        input_glob="derivatives/*_GM_masked.nii.gz",
        out_dir=Path("outputs/hemispec_workflow"),
        device="auto",          # "auto", "cuda", or "cpu"
    )
)

print(result.out_dir)
print(result.hemi_maps_dir)          # final ANS.L / ANS.R / RNS.L / RNS.R maps
print(result.subject_summary_csv)    # per-subject voxel-wise means
```

ROI export is enabled by default when an atlas is available. Set `export_roi_table=False` only when you want voxel-wise maps and subject summaries without ROI features.

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

Wheel/PyPI installs keep large model binaries outside the wheel. The workflow downloads missing released DGN checkpoints automatically on first use unless automatic downloads are disabled. You can also pre-download assets explicitly:

```python
from hemispec import ensure_default_classifier_models, ensure_default_dgn_models

# Returns the DGN model root (.../models/dgn).
dgn_root = ensure_default_dgn_models()

# Optional: classifier bundle for hemisphere-classifier validation.
classifier_dir = ensure_default_classifier_models(mode="single")
```

Then pass those paths into the workflow when you want explicit control:

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

Provide an atlas to create ROI-level features for statistical models or machine-learning classifiers. The long table stores one row per subject / map / ROI; the wide table stores one row per subject with feature columns such as `ANS.L_roi_1` or `RNS.R_roi_180`.

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

## Lower-level inference and metric APIs

Use these only when you need a custom pipeline layout, a single DGN direction, or ANS/RNS computation from already reconstructed maps.

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

## Synthetic smoke test from Python

For documentation, CI, or environment checks that should not download model weights or touch private MRI data:

```python
from pathlib import Path
from hemispec import run_synthetic_quickstart

run_synthetic_quickstart(Path("outputs/hemispec_quickstart"))
```

## What is intentionally not public API

Training code, private manuscript analyses, and raw-data preprocessing decisions are not exposed as stable public Python API. For new user-facing work, document examples with `from hemispec import ...` and keep CLI/GUI examples aligned with the same package-installed environment.
