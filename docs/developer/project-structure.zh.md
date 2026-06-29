# 项目结构

HemiSpec Toolkit 被组织为一个可部署的 Python 包以及已批准的可复用模型资产。公开仓库应使运行时契约清晰，同时不提交私有 MRI 数据或生成输出。

```text
.
|-- src/hemispec/                         # 可导入包：API、CLI、GUI、工作流
|   `-- resources/preprocess/             # 小型打包预处理辅助脚本
|-- tests/                                # 合成/单元回归测试
|-- examples/                             # 公开安全示例和 IO 契约
|   |-- synthetic_quickstart/             # 生成的玩具 NIfTI 示例
|   `-- input_sample/                     # 本地/已批准输入占位符
|-- docs/                                 # 开发者、架构、部署和方法说明
|-- scripts/                              # 发布和本地启动器辅助工具；无核心运行时逻辑
|   `-- research/                         # 本地研究工具，非公开运行时 API
|-- assets/                               # 已批准模型包和本地资产清单
|   |-- atlases/glasser/                  # 本地 Glasser atlas + 标签表，未批准则不追踪
|   `-- models/                           # 已批准 DGN/分类器包，通过 Git LFS 追踪
|-- data/                                 # 本地验证数据，不追踪
|-- outputs/                              # 生成输出，不追踪
|-- reference/                            # 论文/参考材料/训练参考，不追踪
|-- pyproject.toml                        # 包元数据和工具配置
|-- MANIFEST.in                           # 源码发行版包含/排除政策
|-- CONTRIBUTING.md                       # 工程和验证规则
`-- CHANGELOG.md                          # 发布历史
```

## 公开源码与本地资产

已追踪的公开源码应包含：

- `src/hemispec/` 包代码和小型包自有资源。
- 基于合成/小型生成固件的测试。
- README、文档、示例、发布脚本和清单模板。
- 描述预期本地放置位置的资产 README 文件。
- 通过 Git LFS 追踪的已批准可复用 DGN 检查点和分类器包。

被忽略的本地/私有材料包括：

- 真实受试者级 MRI/NIfTI 文件；
- 未批准的模型检查点或分类器包；
- 除非明确批准再发行，否则包括 atlas 有效载荷文件；
- 生成输出、缓存文件夹和编译发布文件夹。

## 运行时资产发现

模型和 atlas 发现集中在 `hemispec.paths` 中，按以下顺序进行：

1. 提供时的显式 CLI/API/GUI 覆盖。
2. 如 `HEMISPEC_DGN_MODEL_ROOT` 等环境变量。
3. 存在时 `assets/` 下的本地项目资产。
4. 首次运行模型下载填充的每用户缓存。
5. 仅用于兼容性的旧版根文件夹，如 `outputs_bi_stable_L/R`。

PyPI 包保持轻量，不嵌入大型 DGN 检查点、分类器包、atlas 有效载荷或受试者级示例。已发布的 DGN/分类器默认值在需要时下载到用户缓存。编译应用发行版可在应用文件夹旁边附带已批准的离线资产（带清单和校验和）。
