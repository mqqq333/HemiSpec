# DGN 推理

本教程使用当前源码检出中的模型文件，对预处理灰质图运行一个方向的已发布 HemiSpec DGN。

## 安装与本地模型资产

先按照[安装](../installation.md)使用 Git LFS 克隆仓库，再从仓库根目录拉取检查点并安装 model 额外依赖：

```bash
git lfs install
git lfs pull
python -m pip install -e ".[model]"
```

当前检出应包含：

```text
assets/models/dgn/outputs_bi_stable_L/ckpts/best_netG_L.pth
assets/models/dgn/outputs_bi_stable_R/ckpts/best_netG_R.pth
```

该源码检出流程直接使用这些本地文件，不需要运行 `hemispec models --install`。

## 输入与空间质控

输入必须是符合[输入与预处理](../input-preprocessing.zh.md)要求的 `*_GM_masked.nii.gz` 文件。推理前必须核对标准 FSL MNI152 1.5 mm 空间网格：形状为 `121 x 145 x 121`，体素大小为 `1.5 x 1.5 x 1.5 mm`，方向一致，并且完整 affine 一致。仅文件名或维度相同不能证明空间兼容。

检查点布局和模型方向映射见[模型包](../reference/model-bundles.zh.md)。

## CLI 示例

在新的输出目录中运行从左到右的推理：

```bash
hemispec infer \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --model-root "assets/models/dgn" \
  --direction L_to_R \
  --out-dir "outputs/dgn_inference_l2r" \
  --device auto
```

运行相反方向时应使用新的目录，避免混合不同检查点的输出：

```bash
hemispec infer \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --model-root "assets/models/dgn" \
  --direction R_to_L \
  --out-dir "outputs/dgn_inference_r2l" \
  --device auto
```

## Python API 示例

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

`run_dgn_inference()` 在内存中返回输出路径；CLI 会打印输出数量和路径。两个接口都不会写出运行清单。

## 实际输出行为

对于 `derivatives/sub-001_GM_masked.nii.gz`，默认输出为：

```text
outputs/dgn_inference_l2r/sub-001_GM_masked_PRED_LR_full.nii.gz
```

输出保持输入 NIfTI 的完整网格，其中目标裁剪区由模型重建，经过阈值处理的源裁剪区从输入复制；目标裁剪区内位于目标掩膜外的体素仍保留输入值。返回记录是路径，不是持久化的源/目标记录表或运行清单。

请手动记录每次运行的来源信息，至少保存 HemiSpec commit 和检查点哈希：

```bash
git rev-parse HEAD > outputs/dgn_inference_l2r/hemispec_commit.txt
sha256sum assets/models/dgn/outputs_bi_stable_R/ckpts/best_netG_R.pth \
  > outputs/dgn_inference_l2r/checkpoint.sha256
```

`L_to_R` 模型包解析到 `outputs_bi_stable_R/ckpts/best_netG_R.pth`，因为目标半球是右侧。在 PowerShell 中请使用 `Get-FileHash -Algorithm SHA256` 代替 `sha256sum`。
