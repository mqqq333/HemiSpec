# DGN 模型包说明

本文档记录 HemiSpec 应为推理部署的训练好的 DGN 资产。模型训练不是 HemiSpec v1 的一部分。

## 范围

`train_code/` 仅作参考材料。使用它来了解：

- `Generator` 架构，
- PyTorch 检查点格式，
- 经过更正的半球裁剪约定，
- 生成的半球补丁如何被粘贴回用于检查。

不要在 v1 中将训练作为用户界面功能暴露，也不要要求用户运行 `train_code/train.py`。

## 方向映射

在 API、CLI、GUI 和文档中使用此经所有者确认的映射：

```text
outputs_bi_stable_L = R_to_L = 右半球 -> 生成左半球
outputs_bi_stable_R = L_to_R = 左半球 -> 生成右半球
```

## 运行时契约

包自有推理适配器应：

1. 加载完整预处理的 `*_GM_masked.nii.gz` NIfTI。
2. 裁剪源半球。
3. 运行匹配的训练好的 `Generator` 检查点。
4. 将生成的补丁粘贴到目标半球位置。
5. 使用原始仿射变换/头信息保存重建的全体积 GM 图。

## 检查点格式

生成器检查点是具有以下形状的 PyTorch 文件：

```python
{
    "epoch": <int>,
    "state_dict": <Generator state dict>,
}
```

## 裁剪

使用经过更正的解剖学约定：

```text
解剖学右侧：z 5:60,   y 15:134, x 15:102
解剖学左侧：z 60:115, y 15:134, x 15:102
```

## 阈值

参考数据集代码在推理前使用以下阈值掩膜低值体素：

```text
img > 0.05
```

ANS/RNS 计算后续使用：

```text
GM >= 0.15
```

请在参数名称和文档中保持这些阈值的分离。
