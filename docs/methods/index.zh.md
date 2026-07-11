# 方法概述

HemiSpec 文档将已发表方法、软件实现和下游扩展分开说明。

## 已发表框架

Wang 等人（2024）提出了跨半球深度生成网络：利用对侧半球预测目标半球，并根据实际图与重建图之间的差异计算体素级指标。

原论文中的指标名称为：

- **ANS — absolute neuroanatomical specificity（绝对神经解剖特异性）：**重建残差所反映的半球特异信号绝对量。
- **RNS — relative neuroanatomical specialization（相对神经解剖特化）：**相对于局部实际/重建幅度归一化后的重建差异。

完整文献见[引用](../citation.md)。

## HemiSpec 实现层

HemiSpec 提供：

- 有文档说明的 T1→GM FSL 预处理路径；
- 可复用的已发布 DGN 推理模型包；
- 双向重建与 ANS/RNS 导出；
- 可选 ROI 聚合；
- 可选半球分类器与 TRT 验证；
- CLI、GUI、Python API、测试、文档与发布工具。

这些软件组件不能被表述为 DGN 或 ANS/RNS 方法的原创来源。

## 下游分析

ANS/RNS 图和 ROI 特征可用于人口学分析、半球身份分类、行为表型关联和疾病组–对照组比较。每一种下游分析都需要独立的研究设计、混杂控制、验证和引用；存在 HemiSpec 命令本身并不自动证明其在新队列中的科学有效性。
