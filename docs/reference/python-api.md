# Python API

The preferred public Python import path is `hemispec`. Use `hemispec` for public Python examples.

The symbols shown here were checked against the current migration toolkit interface on 2026-06-28. Re-check them before public release if the toolkit source or package name changes.

## Preferred public import

```python
from pathlib import Path
from hemispec import MetricComputeConfig, ValidationConfig
from hemispec import compute_metrics, validate_specificity

metrics = compute_metrics(
    MetricComputeConfig(
        actual_glob="/data/gm/*_GM_masked.nii.gz",
        reconstructed_glob="/data/recon/*_PRED_LR_full.nii.gz",
        out_dir=Path("/data/hemispec/metrics"),
        save_subject_maps=True,
    )
)

validation = validate_specificity(
    ValidationConfig(
        maps_dir=metrics.subject_maps_dir,
        out_dir=Path("/data/hemispec/specificity"),
        hemis=("L", "R"),
    )
)
```

