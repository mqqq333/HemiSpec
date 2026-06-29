# 外部资产包

HemiSpec 源码现已通过 Git LFS 在 `assets/models/` 下包含已批准的可复用 DGN 检查点和半球分类器包。Wheel/PyPI 安装将这些大型二进制文件保留在 wheel 之外，可将其下载到用户缓存。外部资产包仍适用于离线安装、自定义模型包、atlas 有效载荷、真实样本数据或编译应用发行版。

## 推荐布局

```text
HemiSpec-Assets/
  ASSET_MANIFEST.yml
  SHA256SUMS.txt
  LICENSES/
  models/
    dgn/
      <左到右包>/ckpts/<检查点名>.pth
      <右到左包>/ckpts/<检查点名>.pth
    hemisphere_classifier/
      <分类器包>/
  atlases/
    glasser/
      <glasser-atlas>.nii.gz
      <glasser-label-table>.xlsx
```

## 清单契约

`ASSET_MANIFEST.yml` 应记录足够的信息，让其他实验室判断该包是否与其工作流兼容：

```yaml
asset_bundle: HemiSpec-Assets
version: 0.1.0
date: 2026-06-29
compatible_with:
  package: hemispec-toolkit
  version: ">=0.1.0,<0.2"
contents:
  dgn_models:
    root: models/dgn
    directions: [L_to_R, R_to_L]
  hemisphere_classifier:
    root: models/hemisphere_classifier
  glasser_atlas:
    atlas: atlases/glasser/<glasser-atlas>.nii.gz
    label_table: atlases/glasser/<glasser-label-table>.xlsx
provenance:
  source: <数据集/训练/来源摘要>
  preprocessing: <所需预处理假设>
license:
  assets: <许可证或再发行限制>
  citations:
    method:
      - Wang et al. 2024, Patterns, https://doi.org/10.1016/j.patter.2024.100930
    assets:
      - <资产特定引用或 DOI>
checksums:
  file: SHA256SUMS.txt
```

## 运行时配置

推荐使用显式 CLI/GUI 路径以确保可复现的运行。环境变量适用于本地默认值：

```text
HEMISPEC_ASSET_ROOT
HEMISPEC_DGN_MODEL_ROOT
HEMISPEC_CLASSIFIER_MODEL_DIR
HEMISPEC_GLASSER_ATLAS
HEMISPEC_GLASSER_LABEL_TABLE
```

解析顺序：显式 CLI/GUI 路径 > 环境变量 > 本地仓库约定 > 每用户缓存。`HEMISPEC_MODEL_CACHE`、`HEMISPEC_MODEL_ASSET_BASE_URL`、`HEMISPEC_AUTO_DOWNLOAD_MODELS` 和 `HEMISPEC_DISABLE_MODEL_AUTO_DOWNLOAD` 控制内置模型缓存/下载路径。

## 发布检查清单

发布资产包前请验证：

- 除非明确批准再发行，否则不包含原始或含受试者标识的 MRI 数据；
- 每个模型、atlas、分类器和标签表在 `SHA256SUMS.txt` 中都有校验和；
- 许可证和引用要求在 `LICENSES/` 或清单中存在；
- 预处理假设和兼容的 HemiSpec 版本已说明；
- 该包与从 [https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0](https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0) 下载的轻量 HemiSpec 版本兼容；
- 该包通过 GitHub Releases、Zenodo、OSF 或机构存储等显式发布渠道发布。

## 运行时边界

轻量 Windows CLI/GUI 产物不打包 PyTorch、atlas 有效载荷、真实 MRI 输入或生成输出。启用模型的工作流需要包含 PyTorch 的 Python 环境。已发布的 DGN/分类器模型默认值可来自 Git-LFS 源码检出、每用户自动下载缓存或显式配置的离线资产包。

## 相关页面

- [数据与模型](../data-and-models.md)
- [发布产物](../release-artifacts.md)
- [v0.1.0 发布验证](../developer/release-verification-v0.1.0.md)
- [路线图](../developer/roadmap.md)
