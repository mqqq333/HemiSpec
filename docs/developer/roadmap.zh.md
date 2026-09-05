# 路线图

本页追踪 v0.1.0 首个公开测试版之后面向公众的 HemiSpec 开发。

## 当前状态

HemiSpec v0.1.0 于 2026-06-28 作为 GitHub 预发布版发布：[https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0](https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0)。它是研究软件/公开测试版，不是成熟的临床或商业产品。

归档版本包含 `hemispec` CLI、`hemispec-gui` 入口点、wheel/sdist 和 Windows CLI/GUI 产物。当前 `main` 另外加入了合成快速测试和模型缓存下载代码。公开文档对应当前源码，这些新增功能不属于归档发行包。

## v0.1.x 优先事项

1. 为当前功能发布新的版本号和不可变标签。独立验证新 wheel、CLI、GUI 和合成快速测试，并保留归档 [v0.1.0 验证记录](release-verification-v0.1.0.md)。
2. 在推理前完成输入校验：检查模型要求的网格和 affine，拒绝重复的受试者/session 标识，并提前检查分类器 atlas、特征和可选依赖。
3. 按运行隔离输出并保障重跑安全：防止旧受试者混入汇总，将快速测试的清理范围限制为自身生成文件。
4. 修复分类器缓存下载地址，加载前校验缓存模型哈希，并为可复用资产发布带版本的兼容性和来源清单。
5. 为并列值 Spearman 相关、非对称 TRT 矩阵及保留有效零残差的 ROI 掩膜补充回归测试。
6. 将 GUI 取消操作传递到分类器/TRT 阶段，改善缺失资产诊断。
7. 增加可选的研究策略，将半球分类验证设为必须步骤。在该策略实现并测试前，分类仍为可选；TRT 始终需要重复扫描。

## v0.2 候选功能

- 在发布元数据、项目所有权和上传检查完成后再将 `hemispec-toolkit` 发布到 PyPI；在此之前继续通过 GitHub Release 分发。
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
