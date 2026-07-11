# DGN 模型包

HemiSpec v0.1.0 为推理部署训练好的生成器检查点。模型训练仅作参考，不是公开工作流的运行要求。

ANS/RNS 与跨半球 DGN 框架源自 Wang 等人（2024），详见[引用](../citation.md)。

## 当前资产布局

```text
assets/models/dgn/
├── outputs_bi_stable_L/
│   └── ckpts/
│       └── best_netG_L.pth       # R_to_L，目标为左半球
└── outputs_bi_stable_R/
    └── ckpts/
        └── best_netG_R.pth       # L_to_R，目标为右半球
```

运行时也支持 `best_netG_R2L.pth` 和 `best_netG_L2R.pth` 等显式方向文件名；两种命名同时存在时优先使用显式方向名。

公开模型包只能包含已批准的运行时资产，不能包含受试者级重建图或训练指标结果。

## 方向映射

```text
outputs_bi_stable_L = R_to_L = 右半球输入 -> 生成左半球
outputs_bi_stable_R = L_to_R = 左半球输入 -> 生成右半球
```

`discover_local_dgn_bundles()` 为 API、CLI 和 GUI 实现这一映射。

## 运行时契约

对于一个方向，推理适配器：

1. 加载预处理 `*_GM_masked.nii.gz`；
2. 应用低值推理掩膜；
3. 裁剪源半球；
4. 加载匹配的生成器检查点；
5. 预测目标半球补丁；
6. 将预测结果放回原始全脑网格；
7. 使用输入 affine/header 保存重建 NIfTI。

双向工作流运行两个方向并合并目标侧结果。

## 检查点格式

支持的生成器检查点可以是直接 state dictionary，也可以是包含 `state_dict` 的封装。运行时加载器会先标准化支持的格式，再加载生成器架构。

期望的单通道补丁形状：

```text
55 × 119 × 87
```

## 裁剪

```text
解剖学右侧：z 5:60,   y 15:134, x 15:102
解剖学左侧：z 60:115, y 15:134, x 15:102
```

这些常量由软件包运行时代码维护。

## 阈值

```text
DGN 输入清理：值 > 0.05
ANS/RNS 有效 GM：值 >= 0.15
```

两个阈值服务于不同阶段，必须分别命名和报告。

## 输出命名

方向特定的全脑重建图使用：

```text
<subject>_PRED_LR_full.nii.gz
```

双向工作流随后在 `voxel_maps/` 下写出最终半球特定指标图。
