# ANS/RNS 方法和指标说明

## 项目边界

HemiSpec v1 只部署训练好的 DGN 模型，不包含模型训练、重新训练或微调功能。

本项目要支持：

```text
1. 使用训练好的 DGN 从预处理 GM map 生成半球重建 GM map
2. 从 GM 和 DGN-reconstructed GM 计算 ANS/RNS
3. 检验 ANS/RNS 的 test-retest reliability
4. 检验 ANS/RNS 的 structural specificity
```

本项目 v1 不做：

```text
1. DGN/GAN/model training
2. model retraining 或 fine-tuning
3. model ablation 或 model comparison
4. 把 train_code/ 暴露为用户入口
```

`train_code/` 只用于开发者理解模型结构、半球 crop 规则和 checkpoint 格式。正式 API、CLI 和 GUI 应调用 `src/hemispec/` 中的运行时代码。

## 预处理输入

DGN 推理和 ANS/RNS 计算都要求先完成 GM 预处理。参考脚本：

```text
src/hemispec/resources/preprocess/process_single_subject_GM_v2_reorient.sh
```

预期输入文件通常命名为：

```text
*_GM_masked.nii.gz
```

示例输入位于：

```text
examples/input_sample/
```

## DGN 推理

当前确认的模型方向：

```text
outputs_bi_stable_L = R_to_L = right hemisphere -> generated left hemisphere
outputs_bi_stable_R = L_to_R = left hemisphere  -> generated right hemisphere
```

解剖半球 crop 规则：

```text
left:  z 60:115, y 15:134, x 15:102
right: z 5:60,   y 15:134, x 15:102
```

推理阶段低值 mask 阈值来自参考 dataset 逻辑：

```text
img > 0.05
```

这个阈值和 ANS/RNS 计算的 GM 阈值不同，不应混用。

## ANS/RNS 公式

对每个体素：

```text
ANS = abs(GM - recon)
RNS = abs(GM - recon) / (abs(GM) + abs(recon) + eps)
```

默认参数：

```text
GM threshold = 0.15
eps          = 1e-6
```

有效体素定义：

```text
finite(GM) and finite(recon) and GM >= 0.15
```

默认不做 s8mm smoothing。

## Test-Retest Reliability

对同一批被试的两个 session/run：

```text
scan A: subject_i session A 的 ANS/RNS map
scan B: subject_i session B 的 ANS/RNS map
```

计算 scan A 和 scan B 的相似度矩阵：

```text
S[i, j] = similarity(scanA_subject_i, scanB_subject_j)
```

默认相似度：

```text
Pearson correlation
```

对角线表示 within-subject test-retest similarity，非对角线表示 between-subject similarity。

## Structural Specificity

Structural specificity 使用同一个相似度矩阵，但解释重点不同。如果 ANS/RNS 反映个体结构特异性，同一被试跨 session 的 ANS/RNS pattern 应该比不同被试更相似。

核心指标：

```text
within_mean        = mean(diagonal(S))
between_mean       = mean(off-diagonal(S))
specificity_index  = within_mean - between_mean
top1_match_rate    = argmax(S[i, :]) 是否为 i
Cohen_d            = within vs between 的效应量
Welch_t_test       = within vs between 的统计检验
```

## Mask 口径

默认使用 rate mask：

```text
rate[v] = mean(abs(X[:, v]) > thr)
keep voxel if rate[v] >= rate_thr
```

默认：

```text
thr      = 0
rate_thr = 0.3
```

这和旧 TRT 流程保持一致，适合避免单个 session 的 mask 导致向量长度不一致。
