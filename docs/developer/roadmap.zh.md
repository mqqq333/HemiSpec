# 路线图

本页追踪 v0.1.0 首个公开测试版之后面向公众的 HemiSpec 开发。

## 当前状态

HemiSpec v0.1.0 于 2026-06-29 作为 GitHub 预发布版发布：[https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0](https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0)。它是研究软件/公开测试版，不是成熟的临床或商业产品。

该版本包含统一的 HemiSpec 仓库、文档网站、`hemispec` CLI、`hemispec-gui` 入口点、wheel/sdist、Windows CLI/GUI 产物、合成快速入门、CI/文档关卡和外部资产分发政策。

## v0.1.x 优先事项

1. 保持发布可下载和可复现：对发布资产进行校验和验证，冒烟测试 CLI，并从已发布 wheel 运行合成快速入门。基线于 2026-06-29 建立；见 [v0.1.0 发布验证](release-verification-v0.1.0.md)。
2. 使首次运行文档更清晰：突出下载链接、快速入门路径和资产/模型边界。
3. 强化资产处理：通过 Git LFS 和首次运行缓存下载保持已批准 DGN/分类器包的可复用性；保持用于 atlas 和自定义/离线包的清单/校验和/许可证/出处模板。
4. 改进 GUI 诊断：设置状态卡现已将 DGN 模型、Glasser atlas、分类器包和 PyTorch 可用性报告为已找到/未找到/下载待处理；下一步是校验和显示和更丰富的首次运行指导。
5. 改进缺失模型、缺失 atlas 文件、缺失分类器包和缺失可选依赖项的错误消息和日志。

## v0.2 候选功能

- 发布 `hemispec-toolkit` 到 PyPI。
- Zenodo DOI 或等效的存档软件引用。
- 超出默认已发布模型缓存的更丰富 atlas/自定义包下载器或解析器。
- 小型已批准演示数据集（如果允许再发行）。
- 一键 HTML/PDF 报告生成。
- 自动构建并上传 Windows 产物的发布 CI。
- 更强的分类器/TRT 输出解释文档。
- 论文公开/存档 DOI 后的稿件、引用和数据可用性页面。

## 追踪源码的非目标

不要向源码仓库添加未批准的模型权重、atlas NIfTI 文件、真实 MRI 输入、生成输出、私有路径或未发表的稿件专用有效载荷。`assets/models/` 下已批准的可复用 DGN/分类器包是明确的 Git-LFS 例外；请单独发布任何额外资产（附清单和校验和）。

## 相关页面

- [v0.1.0 发布验证](release-verification-v0.1.0.md)
- [发布产物](../release-artifacts.md)
- [外部资产包](../reference/asset-bundle.md)
