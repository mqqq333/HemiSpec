# 项目结构

HemiSpec 由可安装的 Python 软件包和经过明确批准的运行时资产组成。公开仓库应完整说明软件与文件契约，但不能公开私有 MRI 数据、研究生成结果，或尚未获准再分发的资产。

```text
.
|-- src/hemispec/                         # Python API、CLI、GUI 与工作流
|   `-- resources/preprocess/             # 包内预处理辅助脚本
|-- tests/                                # 合成/单元回归测试
|-- examples/
|   |-- synthetic_quickstart/             # 可公开再分发的合成 NIfTI 示例
|   `-- input_sample/                     # 本地且被 Git 忽略的 MRI 输入目录；仅 README 公开
|-- docs/                                 # 用户、方法、参考与开发者文档
|-- scripts/                              # 发布和本地启动辅助脚本
|   `-- research/                         # 本地研究工具，不属于公开运行时 API
|-- assets/
|   |-- atlases/glasser/                  # 公开 README/清单；atlas 载荷获批前仅保留本地
|   `-- models/                           # 通过 Git LFS 跟踪的已批准 DGN/分类器包
|-- data/                                 # 本地验证数据，不跟踪
|-- outputs/                              # 生成结果，不跟踪
|-- reference/                            # 本地论文/训练参考资料，不跟踪
|-- pyproject.toml                        # 软件包元数据与工具配置
|-- MANIFEST.in                           # 源码发行包包含/排除策略
|-- CONTRIBUTING.md                       # 工程与验证规则
`-- CHANGELOG.md                          # 发布历史
```

## 公开源码与仅限本地的材料

公开跟踪的内容可以包括：

- `src/hemispec/` 下的软件包代码和小型包内资源；
- 基于合成或小型生成固件的测试与示例；
- README、文档、发布脚本和清单模板；
- 说明本地放置方式与出处字段的资产 README；
- 通过 Git LFS 放在 `assets/models/` 下的已批准 DGN 与分类器包。

以下材料必须保持本地且被忽略，除非已经记录明确的发布批准和再分发权利：

- 真实受试者级 MRI/NIfTI，包括放入 `examples/input_sample/` 的文件；
- 生成的重建图、ANS/RNS 图、ROI 表和验证结果；
- 未批准的模型检查点或分类器包；
- atlas NIfTI 和标签表；
- 私有路径、受试者标识、凭据和未发表结果摘要。

公开可运行示例是 `examples/synthetic_quickstart/`；`examples/input_sample/` 仅是本地输入位置，不能当作可公开再分发的示例数据。

## 运行时资产发现

模型与 atlas 的发现由 `hemispec.paths` 集中管理，顺序如下：

1. 显式 CLI/API/GUI 路径；
2. `HEMISPEC_DGN_MODEL_ROOT` 等环境变量；
3. 存在时使用项目本地 `assets/`；
4. 模型下载写入的用户缓存；
5. 仅为兼容保留的 `outputs_bi_stable_L/R` 等旧目录。

发布 wheel 保持轻量：只包含软件包代码和小型资源，不嵌入大型模型检查点、atlas 载荷或受试者级示例。在当前 `main` 中，DGN 检查点可来自 Git-LFS 源码检出、用户缓存或显式配置的离线资产包。分类器缓存下载目前并不完整，分类器资产需要来自 Git-LFS 检出或显式本地目录；详见[数据与模型](../data-and-models.md)。归档 `v0.1.0` wheel 不包含当前下载器。
