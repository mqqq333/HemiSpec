# 软件概述

HemiSpec 被组织为软件包优先的生态系统，而非一组独立脚本。当前文档面向从 `main` 安装源码；旧版本保留在 [GitHub Releases 页面](https://github.com/mqqq333/HemiSpec/releases)，PyPI 项目尚未公开。Python 包是主要产物；CLI 和 GUI 入口点均基于同一公开 API 构建。

<figure markdown="span">
  ![HemiSpec 工作流概览](assets/figures/hemispec-workflow-overview-ai.png){ width="100%" }
  <figcaption>HemiSpec 遵循从输入 GM 到重建、差异分析和半球特异性指标的公开工作流序列，然后将这些输出扩展为 ROI 表、验证和发布产物。</figcaption>
</figure>

## 用户界面层

| 层 | 公开名称 | 状态 | 用途 |
| --- | --- | --- | --- |
| Python 包 | `hemispec-toolkit` | 主要公开产物 | 安装到当前 Python/PyTorch 环境中的 API 和 CLI/GUI 入口点。 |
| CLI | `hemispec` | 软件包入口点 | 适用于服务器和集群的脚本化工作流。 |
| GUI | `hemispec-gui` | 软件包入口点 | 从同一 PyTorch 环境启动，用于 ANS/RNS 生成、可选 ROI 表和可选验证的桌面启动器。 |
| 编译应用 | HemiSpec Desktop / HemiSpec Model App | 构建目标 | 从源码检出构建的可选文件夹发行版。 |

<figure markdown="span">
  ![HemiSpec GUI 预览](assets/figures/hemispec-gui-preview.png){ width="100%" }
  <figcaption>当前紧凑 GUI 预览，使用公开安全的占位符路径。GUI 是 `hemispec workflow` 之上的薄层启动器。</figcaption>
</figure>

## 当前 GUI 范围

默认 GUI 范围有意保持精简，仅暴露普通用户获取 ANS/RNS 图所需的决策：

- 预处理 GM 输入 glob，
- 输出工作区，
- 可选 ROI 表导出（含 atlas 和标签表路径），
- 可选半球分类器验证，
- 可选 TRT 可靠性，
- 运行/打开/复制 CLI/日志控件。

模型检查点、设备选择、阈值、后缀规则、分类器包路径或 TRT 正则表达式不在 GUI 中暴露，这些高级设置仍可通过 CLI/API 使用，以保持 GUI 的可复现性和易维护性。

## 当前发布分类

- **当前源码包**：提供 CLI、紧凑 GUI 启动器、计算、ROI 导出、验证和检查，不打包受试者数据或未批准 atlas 资产。
- **启用模型的环境**：使用 Git LFS 检出或显式批准的本地 DGN 与分类器资产运行端到端 DGN 推理和 ANS/RNS 工作流。当前 `main` 可从 Git LFS media 缓存下载 DGN 检查点，但不能下载完整分类器包；详见[数据与模型](data-and-models.md)。

Atlas 文件对 ROI 导出仍是可选项，但已发布分类器要求兼容的 Glasser 1.5 mm atlas，以及左侧 `1..180` / 右侧 `1001..1180` 标签；自定义 atlas 仅用于 ROI。公开构建不应静默打包私有资产。

ANS/RNS 与跨半球 DGN 框架源自 Wang 等人（2024），详见[引用](citation.md)。
