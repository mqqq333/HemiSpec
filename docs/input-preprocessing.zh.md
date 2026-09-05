# 输入与预处理

本页明确说明：如何把 T1 加权结构像转换为已发布 HemiSpec DGN 模型所需的输入。

## 不要混淆两种输入

| 工作流边界 | 接受的输入 |
| --- | --- |
| `process_single_subject.sh` | 每名受试者一张原始或最小预处理的 T1 加权 NIfTI，通常命名为 `*_T1w.nii.gz` |
| HemiSpec DGN 工作流 | 每名受试者一张已预处理、MNI 空间、掩膜后的灰质图，通常命名为 `*_GM_masked.nii.gz` |

!!! danger "不要把原始 T1 直接传给 `hemispec workflow`"
    原始 T1 强度图、未去颅骨 T1、native 空间组织图或位于其他模板网格的图，都不是已发布 DGN 检查点的有效输入。

## 科学预处理契约

Wang 等人（2024）对原始方法的预处理要求包括：将 T1 加权图像分割为不同组织；把 GM 密度图标准化到 MNI 空间的 `1.5 × 1.5 × 1.5 mm³` 分辨率；把值归一化到 `0–1`；使用 GM 概率阈值 `0.15` 提取灰质体素，然后再进行半球分割与裁剪。

项目根目录的 `process_single_subject.sh` 使用 FSL BET、FAST、FLIRT 和 `fslmaths` 实现上述输入准备。该脚本是本项目的具体操作实现；原始科学框架和预处理要求仍应归因并引用 Wang 等人（2024）。

## 研究主脚本

研究流程使用的脚本位于仓库根目录：

```text
process_single_subject.sh
```

该脚本基于 Bash，并要求可用的 FSL 环境。在 Windows 上，建议在 Linux、WSL、HPC 或其他支持 FSL 的环境中完成预处理；生成的 NIfTI 文件随后可在 Windows 或 Linux 中交给 HemiSpec。

Python 包内还包含一个增强变体：

```text
src/hemispec/resources/preprocess/process_single_subject_GM_v2_reorient.sh
```

该变体增加了显式重定向，并先用去颅骨 T1 估计 T1→MNI 仿射，再将变换应用到 GM 部分体积图。**同一队列内不要混用两个预处理版本。**研究方案中应记录准确的脚本文件名和版本。

## 运行前提

运行 `process_single_subject.sh` 前：

1. 安装并验证 FSL。
2. 设置 `FSLDIR` 并加载 FSL 配置。
3. 确认以下参考图存在：

```text
${FSLDIR}/data/standard/MNI152_T1_1.5mm_brain.nii.gz
```

典型 shell 配置：

```bash
export FSLDIR=/path/to/fsl
source "${FSLDIR}/etc/fslconf/fsl.sh"
export PATH="${FSLDIR}/bin:${PATH}"
```

## 处理一名受试者

脚本严格接收两个位置参数：

```text
process_single_subject.sh 输入_T1 输出前缀
```

示例：

```bash
mkdir -p derivatives
bash process_single_subject.sh \
  raw/sub-001_T1w.nii.gz \
  derivatives/sub-001
```

最终 DGN 输入：

```text
derivatives/sub-001_GM_masked.nii.gz
```

处理日志：

```text
derivatives/sub-001_debug.log
```

当前研究脚本在成功处理后会删除 BET、FAST、FLIRT 和掩膜中间产物。如果正式质控记录需要保留中间图，应使用保留中间文件的脚本副本，或在版本控制的研究副本中暂时关闭清理，并记录该变更。

重新处理时使用新的输出前缀。失败的重跑可能留下旧的 `*_GM_masked.nii.gz`，仅凭文件名匹配不能确认最新一次预处理成功。

## `process_single_subject.sh` 的处理步骤

| 步骤 | FSL 命令 | 目的 | 主要输出 |
| --- | --- | --- | --- |
| 1 | `bet -f 0.4 -B` | 去颅骨并进行偏置场/颈部清理 | `<prefix>_T1_bet.nii.gz` |
| 2 | `fast -R 0.3 -H 0.1` | 分割组织概率图 | `<prefix>_seg_pve_1.nii.gz`（GM PVE） |
| 3 | `flirt` | 将 GM 部分体积图仿射配准到 FSL MNI152 1.5 mm 脑模板 | `<prefix>_GM_linear_MNI.nii.gz` |
| 4a | `fslmaths -thr 0.15 -bin` | 创建 GM 概率掩膜 | `<prefix>_GM_mask.nii.gz` |
| 4b | `fslmaths -mul` | 将掩膜应用于 MNI 空间 GM 概率图 | `<prefix>_GM_masked.nii.gz` |
| 5 | `rm` | 最终输出写入后删除中间文件 | 保留最终 GM 图和调试日志 |

## DGN 输入格式

已发布 HemiSpec 检查点和仓库示例采用以下契约：

| 属性 | 期望值 |
| --- | --- |
| 维度 | 每名受试者一张 3D 体数据 |
| 数据类型 | 数值型 NIfTI；仓库示例为 `float32` |
| 数值范围 | 有限的 GM 概率/密度值，通常为 `0–1` |
| 模板 | FSL MNI152 T1 1.5 mm brain |
| 网格 | `121 × 145 × 121` 体素 |
| 体素大小 | `1.5 × 1.5 × 1.5 mm³` |
| 仿射矩阵 | 必须与 FSL 参考图一致；不能只比较维度 |
| 文件名 | 稳定、唯一的受试者标识，加 `_GM_masked.nii.gz` 后缀 |

HemiSpec 通过移除配置的文件后缀获得受试者标识。因此，同一输入 glob 匹配到的每个文件都必须拥有唯一、稳定的前缀。

以上是输入必须满足的条件，不代表软件已自动检查全部条件：当前 DGN 推理不会完整校验模板 affine 或方向。推理前应完成以下检查。

## DGN 推理前的质量控制

不能只检查文件名。每个队列至少应检查：

1. **去颅骨：**无明显残留颅骨/颈部信号，也没有大范围皮层被错误删除。
2. **组织分割：**GM 部分体积图应覆盖皮层和皮层下灰质，而不是 WM/CSF。
3. **MNI 对齐：**转换后的 GM 图应与 MNI152 1.5 mm 参考图良好重叠，无明显平移、旋转、缩放或左右翻转错误。
4. **网格一致性：**所有受试者的 shape、体素大小、方向与 affine 与参考图及彼此一致。
5. **数值范围：**数值有限，通常位于 `0–1`，背景为零。
6. **掩膜质量：**`0.15` 阈值应去除低概率边缘噪声，但不能造成大片 GM 缺失。
7. **全队列目视检查：**BET、FAST 或 FLIRT 失败的个体应在 DGN 推理前排除或重新处理。

常用 FSL 检查：

```bash
fslhd derivatives/sub-001_GM_masked.nii.gz
fslstats derivatives/sub-001_GM_masked.nii.gz -R -V
fsleyes \
  "${FSLDIR}/data/standard/MNI152_T1_1.5mm_brain.nii.gz" \
  derivatives/sub-001_GM_masked.nii.gz
```

Python 检查示例：

```python
import os
from pathlib import Path
import nibabel as nib
import numpy as np

path = Path("derivatives/sub-001_GM_masked.nii.gz")
img = nib.load(path)
reference = nib.load(
    Path(os.environ["FSLDIR"]) / "data/standard/MNI152_T1_1.5mm_brain.nii.gz"
)
data = img.get_fdata(dtype=np.float32)

assert img.shape == reference.shape == (121, 145, 121)
assert np.allclose(img.header.get_zooms()[:3], (1.5, 1.5, 1.5))
assert np.allclose(img.affine, reference.affine, rtol=0, atol=1e-4)
assert nib.aff2axcodes(img.affine) == nib.aff2axcodes(reference.affine)
assert np.isfinite(data).all()
assert data.min() >= 0
assert data.max() <= 1.0 + 1e-5
```

## 批处理示例

```bash
set -e
shopt -s nullglob
mkdir -p derivatives
for t1 in raw/sub-*/anat/*_T1w.nii.gz; do
  subject=$(basename "$t1" _T1w.nii.gz)
  test ! -e "derivatives/${subject}_GM_masked.nii.gz"
  bash process_single_subject.sh "$t1" "derivatives/$subject"
done
```

完成质量控制后运行 HemiSpec：

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_preprocessed \
  --no-roi-table
```

批处理示例会在预处理失败或发现已有最终输出时停止。每次 HemiSpec 运行都使用新的输出目录；重复扫描的文件名应同时保留受试者和 session 标识。

## 不同阶段的阈值

- `process_single_subject.sh` 使用 GM 概率 `0.15` 创建最终掩膜。
- DGN 推理内部还会把低于或等于 `0.05` 的输入值清零；正确生成的 `0.15` 掩膜输入已经比该内部清理更严格。
- ANS/RNS 计算默认使用 `0.15` 作为有效 GM 阈值。

研究方案中应记录这些阈值。修改阈值会改变输入或指标的有效支持范围，应视为方法学变化。

## 预处理引用

报告该工作流时，应同时引用原始 ANS/RNS 框架以及本实现使用的 FSL 方法。完整文献见[引用](citation.md)。
