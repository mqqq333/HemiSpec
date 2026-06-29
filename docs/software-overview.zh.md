# 软件概述

HemiSpec 被组织为一个小型软件生态系统，而非单纯的源码仓库：Python 包、CLI、GUI 入口点和编译好的桌面文件夹均基于同一公开 API 构建。

<figure markdown="span">
  ![HemiSpec 工作流概览](assets/figures/hemispec-workflow-overview-ai.png){ width="100%" }
  <figcaption>HemiSpec 遵循从输入 GM 到重建、差异分析和半球特异性指标的公开工作流序列，然后将这些输出扩展为 ROI 表、验证和发布产物。</figcaption>
</figure>

## 用户界面层

| 层 | 公开名称 | 状态 | 用途 |
| --- | --- | --- | --- |
| Python 包 | `hemispec-toolkit` | 开发中 / wheel 本地构建 | 可安装的 API 和命令入口点。 |
| CLI | `hemispec` | 开发中 / 本地测试通过 | 适用于服务器和集群的脚本化工作流。 |
| GUI | `hemispec-gui` | 紧凑标准工作流 GUI 本地冒烟测试通过 | ANS/RNS 生成、可选 ROI 表和可选验证的桌面启动器。 |
| 编译应用 | HemiSpec Desktop / HemiSpec Model App | 发布目标 | 面向不应管理 Python 环境的用户的文件夹发行版。 |

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

- **轻量包/应用**：CLI、紧凑 GUI、计算、ROI 导出、验证和检查，不打包私有模型/数据资产。
- **启用模型的包/应用**：使用 Git LFS、首次运行缓存下载或显式离线资产中已发布的 DGN/分类器默认值，进行端到端 DGN 推理和 ANS/RNS 工作流；atlas 文件对于 ROI 导出仍是可选的。

默认公开构建应避免静默打包私有 `assets/`；模型和 atlas 包应作为带有校验和、许可证说明和兼容性元数据的显式发布产物。
