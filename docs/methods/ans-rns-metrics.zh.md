# ANS 和 RNS 指标

ANS 和 RNS 是 Wang 等人 2024 年引入的重建衍生特异性指标。HemiSpec 将这些指标作为下游分析的核心表示。

## 定义

对于实际灰质图 `GM` 及其对侧重建对应物 `recon`：

```text
ANS = abs(GM - recon)
RNS = abs(GM - recon) / (abs(GM) + abs(recon) + eps)
```

## 解释

ANS 测量绝对残差幅度。RNS 在考虑局部灰质强度后测量相对残差幅度。

两个指标通常在有效灰质掩膜内逐体素计算，然后可在 atlas ROI 内汇总。

## 引用边界

使用 ANS/RNS 作为指标时，请引用 Wang 等人 2024 年的论文。使用 HemiSpec 特定的下游任务分析工作流时，请在相关稿件或预印本公开后引用 HemiSpec 稿件。
