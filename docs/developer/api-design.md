# HemiSpec API Design

This document defines the first stable Python API layer for the Hemisphere
Reconstruction Structural Specificity Toolkit.

The API is intentionally the foundation layer. CLI, PyPI packaging, and GUI
deployment should call this layer instead of duplicating workflow logic.

## Public package name

Keep the current import name for compatibility:

```python
import hemispec
```

The product name can be presented as `HemiSpec` while the package remains
`hemispec-toolkit` / `hemispec` until release naming is finalized.

## Workflow order

The target product workflow is:

```text
preprocessed GM -> DGN inference -> reconstructed GM -> ANS/RNS -> reliability/specificity validation
```

The preprocessing contract is documented by:

```python
from hemispec import get_preprocessing_spec

spec = get_preprocessing_spec()
print(spec.script_path)
print(spec.sample_input_dir)
```

The expected preprocessing script is:

```text
src/hemispec/resources/preprocess/process_single_subject_GM_v2_reorient.sh
```

It produces `*_GM_masked.nii.gz` files. Example inputs are in:

```text
examples/input_sample/
```

## Metric API

Use `MetricComputeConfig` and `compute_metrics` to compute ANS/RNS maps:

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

This writes:

```text
ANS_group_masked_mean.nii.gz
RNS_group_masked_mean.nii.gz
validN.nii.gz
coverage.nii.gz
subject_maps/<subject>_ANS.nii.gz
subject_maps/<subject>_RNS.nii.gz
```

## Validation API

Use `ValidationConfig` and either `validate_specificity` or
`validate_reliability`:

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

Both functions use the same matrix engine:

```text
within similarity   = diagonal scan-A vs scan-B similarity
between similarity  = off-diagonal similarity
specificity index   = mean(within) - mean(between)
top-1 match rate    = percent of rows whose best match is the same subject
```

`validate_reliability` is an interpretation alias for the same computation when
the inputs are repeat scans.

## DGN inference API

The public contract is already defined:

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

For the common end-to-end workflow, use `PipelineRunConfig` and `run_pipeline`:

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

The local bundle discovery follows the confirmed product-level mapping:

```text
outputs_bi_stable_L = R_to_L = right hemisphere -> generated left hemisphere
outputs_bi_stable_R = L_to_R = left hemisphere  -> generated right hemisphere
```

See `docs/dgn_model_bundle.md` for checkpoint locations, crop conventions, and
current adapter status.

The API now has a package-owned runtime adapter for trained PyTorch Generator
checkpoints. Install the model extra before running real DGN inference:

```bash
python -m pip install -e .[model]
```

`train_code/` remains reference-only. Runtime inference uses package-owned
modules and trained checkpoints, not training scripts. The public model bundle
contract intentionally exposes deployed inference assets rather than training
code paths.

## Bilateral workflow API

For the release workflow, use `BilateralWorkflowConfig` and
`run_bilateral_workflow`. This is the API entry point behind the GUI
`Full Workflow` page and the CLI `hemispec workflow` command.

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

print(run.combined_maps_dir)
print(run.hemi_maps_dir)
print(run.subject_summary_csv)
print(run.roi_csv)       # optional: present when ROI atlas export is enabled and available
print(run.roi_wide_csv)  # optional: present when ROI atlas export is enabled and available
```

The workflow runs both deployed DGN directions:

```text
L_to_R = left hemisphere -> generated right hemisphere
R_to_L = right hemisphere -> generated left hemisphere
```

It combines the generated left and right target hemispheres into bilateral
subject maps, and also writes hemisphere-only maps:

```text
subject_hemi_maps/<subject>_ANS.L.nii.gz
subject_hemi_maps/<subject>_ANS.R.nii.gz
subject_hemi_maps/<subject>_RNS.L.nii.gz
subject_hemi_maps/<subject>_RNS.R.nii.gz
```

When ROI atlas export is enabled and an atlas is available, ROI outputs include
both a long table for the saved classifier adapter and a wide table for direct
downstream use. If no atlas is provided, voxel-wise ANS/RNS maps remain the
primary output and users can extract ROI features with their own downstream
methods:

```text
tables/roi_features_bilateral.csv
tables/roi_features_bilateral_wide.csv
```

The wide table has one row per subject with explicit feature names such as:

```text
ANS.L_roi_1
ANS.R_roi_1
RNS.L_roi_1
RNS.R_roi_1
```

The subject summary table reports hemisphere means and bilateral finite-voxel
means:

```text
ANS.L_mean
ANS.R_mean
RNS.L_mean
RNS.R_mean
ANS.whole_brain_mean
RNS.whole_brain_mean
```

## CLI and GUI rule

```text
CLI args -> config dataclass -> API function
GUI fields -> config dataclass -> API function
```

The CLI follows this rule for `models`, `infer`, `run`, `workflow`, `compute`,
`trt`, `specificity`, and `hemi-classify`.

The GUI now follows the same rule through the HemiSpec workbench pages:

```text
Full Workflow
Single Direction
DGN Inference
Compute ANS/RNS
TRT Reliability
Hemisphere Classifier
Structural Specificity
```

The GUI is intentionally a thin interface over the public API. New workflow
logic should be added to the API first, then exposed through CLI and GUI.
