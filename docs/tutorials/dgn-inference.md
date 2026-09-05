# DGN inference

This tutorial runs one released HemiSpec DGN direction on preprocessed gray-matter maps by using the model files in the current source checkout.

## Install and local model assets

Follow [Installation](../installation.md) to clone the repository with Git LFS. From the repository root, materialize the tracked checkpoints and install the model extra:

```bash
git lfs install
git lfs pull
python -m pip install -e ".[model]"
```

The current checkout should contain:

```text
assets/models/dgn/outputs_bi_stable_L/ckpts/best_netG_L.pth
assets/models/dgn/outputs_bi_stable_R/ckpts/best_netG_R.pth
```

This source-checkout workflow uses those local files. It does not require `hemispec models --install`.

## Inputs and spatial QC

Use preprocessed `*_GM_masked.nii.gz` files that satisfy [Input and preprocessing](../input-preprocessing.md). In particular, verify the canonical FSL MNI152 1.5 mm spatial grid before inference: shape `121 x 145 x 121`, voxel size `1.5 x 1.5 x 1.5 mm`, matching orientation, and matching full affine. A filename or matching dimensions alone do not establish spatial compatibility.

See [Model bundles](../reference/model-bundles.md) for the checkpoint layout and model-direction mapping.

## CLI example

Run left-to-right inference into a new output directory:

```bash
hemispec infer \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --model-root "assets/models/dgn" \
  --direction L_to_R \
  --out-dir "outputs/dgn_inference_l2r" \
  --device auto
```

For the opposite direction, use a fresh directory so outputs from different checkpoints are not mixed:

```bash
hemispec infer \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --model-root "assets/models/dgn" \
  --direction R_to_L \
  --out-dir "outputs/dgn_inference_r2l" \
  --device auto
```

## Python API example

```python
from pathlib import Path

from hemispec import DGNInferenceConfig, discover_local_dgn_bundles, run_dgn_inference

bundles = discover_local_dgn_bundles(Path("assets/models/dgn"))
output_paths = run_dgn_inference(
    DGNInferenceConfig(
        model=bundles["L_to_R"],
        input_glob="derivatives/*_GM_masked.nii.gz",
        out_dir=Path("outputs/dgn_inference_l2r_api"),
        direction="L_to_R",
        device="auto",
    )
)

for path in output_paths:
    print(path)
```

`run_dgn_inference()` returns the output paths in memory. The CLI prints the output count and paths. Neither interface writes a run manifest.

## Actual output behavior

With an input such as `derivatives/sub-001_GM_masked.nii.gz`, the default output is:

```text
outputs/dgn_inference_l2r/sub-001_GM_masked_PRED_LR_full.nii.gz
```

The output is on the input NIfTI's full grid. It contains the reconstructed target crop, while the thresholded source crop is copied from the input; input values remain at target-crop voxels outside the target mask. The returned records are paths, not a persisted source/target record table or manifest.

Record provenance alongside each run yourself. At minimum, retain the HemiSpec commit and checkpoint hash:

```bash
git rev-parse HEAD > outputs/dgn_inference_l2r/hemispec_commit.txt
sha256sum assets/models/dgn/outputs_bi_stable_R/ckpts/best_netG_R.pth \
  > outputs/dgn_inference_l2r/checkpoint.sha256
```

The `L_to_R` bundle resolves to `outputs_bi_stable_R/ckpts/best_netG_R.pth` because the target hemisphere is right. Use `Get-FileHash -Algorithm SHA256` instead of `sha256sum` on PowerShell.
