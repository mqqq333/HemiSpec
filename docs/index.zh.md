# HemiSpec

**HemiSpec** 是一个科研软件工具包，用于将预处理灰质图转换为双侧重建衍生半球指标：**ANS**（absolute neuroanatomical specificity，绝对神经解剖特异性）与 **RNS**（relative neuroanatomical specificity，相对神经解剖特异性）。

!!! important "输入边界"
    HemiSpec 的 DGN **不能直接接收原始 T1 加权 MRI**。每个 T1 图像必须先通过文档中的 FSL 预处理流程，转换为 MNI152 1.5 mm 空间的掩膜灰质图（`*_GM_masked.nii.gz`）。

<p markdown="span">
  [输入与预处理](input-preprocessing.md){ .md-button .md-button--primary }
  [快速开始](quickstart.md){ .md-button }
  [安装](installation.md){ .md-button }
</p>

## 端到端工作流

<figure markdown="span">
  ![跨半球重建与 ANS/RNS 定义](assets/figures/hemispec-study-design.png){ width="100%" }
  <figcaption>基于 Wang 等人（2024）重建框架与 ANS/RNS 定义的原理示意。HemiSpec 从 FSL 预处理后的 GM 图开始；ANS/RNS 为非负的 GM 衍生指标，不是以毫米计量的距离。半球验证为可选步骤，图中的行为表型分析不属于当前内置工作流。</figcaption>
</figure>

| 阶段 | 输入 | 主要处理 | 输出 |
| --- | --- | --- | --- |
| 预处理 | T1 加权 NIfTI | FSL 去颅骨、组织分割、MNI 仿射配准、GM 阈值与掩膜 | `*_GM_masked.nii.gz` |
| 重建 | 预处理 GM 图 | 左到右与右到左 DGN 推理 | 目标半球重建图 |
| 指标计算 | 实际 GM 与重建 GM | ANS/RNS 残差指标 | `ANS.L`、`ANS.R`、`RNS.L`、`RNS.R` |
| 可选汇总 | 体素图 + 兼容 atlas | ROI 聚合 | ROI 长表与宽表 |
| 可选验证 | 图或 ROI 特征 | 半球分类和/或 TRT 分析 | 验证表格与图 |

## 原始方法与 HemiSpec 扩展的边界

跨半球 DGN 框架以及 ANS/RNS 定义源自 **Wang 等人（2024）**。HemiSpec 在该方法基础上提供可安装的 API/CLI/GUI、模型资产发现、双侧图导出、ROI 汇总、验证工具、文档与发布流程。

- 使用原始方法与指标时：引用 Wang 等人（2024）。
- 使用 HemiSpec 软件或下游研究时：在对应公共软件/论文记录发布后另行引用。

完整文献与引用边界见[引用](citation.md)。

## 选择使用路径

<div class="grid cards" markdown>

-   **准备真实 MRI 输入**

    ---

    从 T1 加权 NIfTI 开始，运行 `process_single_subject.sh`，并检查 DGN 输入网格和质量控制项目。

    [输入与预处理](input-preprocessing.md)

-   **运行 HemiSpec**

    ---

    通过 Git LFS 检出并安装当前源码，检查模型就绪状态，再运行 GUI 或双向 CLI 工作流。

    [快速开始](quickstart.md)

-   **理解方法**

    ---

    查看重建框架、原始 ANS/RNS 定义以及 HemiSpec 的数值实现说明。

    [方法](methods/index.md)

-   **模型与 atlas 资产**

    ---

    了解 DGN 检查点、分类器包和可选 ROI atlas 的定位与分发方式。

    [数据与模型](data-and-models.md)

</div>

## 当前软件范围

本站文档对应当前 `main` 分支源码。归档 `v0.1.0` 发行包不包含本站所有命令，例如 `quickstart` 和模型缓存自动安装；详见[安装](installation.md)。PyPI 项目尚未公开。报告软件使用情况时，应记录源码 commit。

GUI 和 CLI 生成体素级 ANS/RNS 图。ROI 表、半球分类器验证和 TRT 验证均为可选步骤。ROI 导出需要与输入网格一致的 atlas；已发布分类器还要求兼容的 Glasser atlas 及标签。每次运行应使用新的输出目录。

---

<p class="site-credits">
  源码：<a href="https://github.com/mqqq333/HemiSpec" target="_blank" rel="noopener">github.com/mqqq333/HemiSpec</a>。文档基于 <a href="https://squidfunk.github.io/mkdocs-material/" target="_blank" rel="noopener">Material for MkDocs</a> 构建。
</p>
