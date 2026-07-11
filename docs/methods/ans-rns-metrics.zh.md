# ANS 与 RNS 指标

ANS 和 RNS 由 Wang 等人（2024）提出，用于描述重建衍生的半球特异性。

## 指标定义与软件解释

对于目标半球实际 GM 值 `Act_i` 与其重建值 `Recon_i`，HemiSpec 按照对 Wang 等人（2024）定义的如下软件化解释进行实现：

```text
ANS_i = abs(Act_i - Recon_i)
RNS_i = abs((Act_i - Recon_i) / (Act_i + Recon_i))
```

- **ANS：**absolute neuroanatomical specificity（绝对神经解剖特异性）。
- **RNS：**relative neuroanatomical specificity（相对神经解剖特异性）。

ANS 表示实际值与重建值之间差异的绝对量；RNS 表示该差异占局部信号的相对比例。

## HemiSpec 数值实现

HemiSpec 计算：

```text
ANS = abs(GM - recon)
RNS = abs(GM - recon) / (abs(GM) + abs(recon) + eps)
```

实现还要求输入值有限，并应用可配置的有效 GM 阈值（默认 `0.15`）。分母中的绝对值和较小的 `eps` 用于在重建值接近零或出现小幅负数值误差时稳定除法。对于非负 GM 与重建值，当 `eps` 趋近于零时，该实现趋近于原论文表达式。

当研究要求精确数值复现时，应报告这一实现细节。

## 解释边界

ANS/RNS 是重建误差衍生量，不是神经功能、因果侧化或组织病理的直接测量。其解释依赖预处理质量、模型适用域、重建行为、掩膜、站点/扫描仪效应以及下游验证。

## 引用边界

指标框架应引用 Wang 等人（2024）；在公共软件记录可用后，HemiSpec 软件实现应另行引用。完整说明见[引用](../citation.md)。
