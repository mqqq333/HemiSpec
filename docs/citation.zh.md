# 引用

HemiSpec 将**原始科学方法**、**预处理软件**与 **HemiSpec 软件/下游研究**的引用分开说明。

## 原始跨半球 DGN 与 ANS/RNS 框架

使用或描述跨半球 DGN 重建方法、ANS 或 RNS 时，应引用：

> Wang, G., Jiang, N., Ma, Y., Suo, D., Liu, T., Funahashi, S., & Yan, T. (2024). Using a deep generation network reveals neuroanatomical specificity in hemispheres. *Patterns, 5*(4), 100930. https://doi.org/10.1016/j.patter.2024.100930

HemiSpec 在公开文档中统一使用以下术语：

- **ANS：**absolute neuroanatomical specificity（绝对神经解剖特异性）。
- **RNS：**relative neuroanatomical specificity（相对神经解剖特异性）。

HemiSpec 文档沿用原论文的名称与缩写。

## FSL 预处理

研究使用的 `process_single_subject.sh` 以及包内的重定向增强变体均使用 FSL、BET、FAST 和 FLIRT。方法部分应引用实际支持预处理的工具：

> Jenkinson, M., Beckmann, C. F., Behrens, T. E. J., Woolrich, M. W., & Smith, S. M. (2012). FSL. *NeuroImage, 62*(2), 782–790. https://doi.org/10.1016/j.neuroimage.2011.09.015

> Smith, S. M. (2002). Fast robust automated brain extraction. *Human Brain Mapping, 17*(3), 143–155. https://doi.org/10.1002/hbm.10062

> Zhang, Y., Brady, M., & Smith, S. (2001). Segmentation of brain MR images through a hidden Markov random field model and the expectation-maximization algorithm. *IEEE Transactions on Medical Imaging, 20*(1), 45–57. https://doi.org/10.1109/42.906424

> Jenkinson, M., & Smith, S. (2001). A global optimisation method for robust affine registration of brain images. *Medical Image Analysis, 5*(2), 143–156. https://doi.org/10.1016/S1361-8415(01)00036-6

## Glasser 皮层分区

使用 Glasser/HCP-MMP atlas 进行 ROI 导出或半球分类时，应引用原始分区论文：

> Glasser, M. F., Coalson, T. S., Robinson, E. C., et al. (2016). A multi-modal parcellation of human cerebral cortex. *Nature, 536*, 171-178. https://doi.org/10.1038/nature18933

MNI 1.5 mm NIfTI 转换版属于派生 atlas 资产，并非原始分区本身。应另行记录其分发者/来源 URL、版本或 commit、获取日期、MNI 模板、体素大小、转换方法和标签映射。不能将 `1..180`、`1001..1180` 等转换版特有的整数标签约定归于原始论文。本地 atlas 的要求见[数据与模型](data-and-models.md)。

## HemiSpec 软件引用

使用软件时，应在公共 HemiSpec 发布/归档记录可用后引用对应记录，并在方法部分保留软件版本。在归档 DOI 尚未注册前，可使用仓库 `CITATION.cff`、发布标签与访问日期。使用当前 `main` 源码检出时，还应报告 `git rev-parse HEAD` 输出的准确 commit；仅凭包版本号无法将其与归档 `v0.1.0` 发布版区分。

不能用软件引用替代 Wang 等人的方法论文：原始科学方法与软件实现是两类独立贡献，应分别致谢和引用。

## HemiSpec 下游论文

“稿件准备中”不是稳定的公共文献。只有在预印本、期刊论文或归档记录公开后，才应将 HemiSpec 下游论文作为正式引用。在此之前，应描述“使用 HemiSpec 完成分析”，并报告准确的软件版本或 commit。

## 建议的方法描述

> T1 加权图像通过基于 FSL 的流程（BET、FAST 和 FLIRT）转换为 MNI152 1.5 mm 灰质概率图，并使用 GM 概率阈值 0.15 进行掩膜后输入 HemiSpec。跨半球重建以及 ANS/RNS 计算遵循 Wang 等人（2024）提出的框架。为保证可复现性，记录软件版本、模型包、阈值和可选验证设置。
