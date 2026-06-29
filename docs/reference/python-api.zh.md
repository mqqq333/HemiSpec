# Python API

首选公开 Python 导入路径为 `hemispec`。公开 Python 示例请使用 `hemispec`。

以下符号已于 2026-06-28 与当前迁移工具包接口核对。如果工具包源码或包名发生变化，请在公开发布前重新核对。

## 首选公开导入

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
