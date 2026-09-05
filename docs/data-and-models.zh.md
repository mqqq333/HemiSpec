# 数据与模型

!!! important "MRI 输入是独立前置条件"
    模型权重和 atlas 文件不会把原始 T1 MRI 自动转换为 DGN 输入。应先为每名受试者准备一张 MNI152 1.5 mm 的 `*_GM_masked.nii.gz`；详见[输入与预处理](input-preprocessing.md)。

当前 `main` 使用两个 DGN 生成器检查点、可选的半球分类器包，以及用于 ROI 导出的可选 atlas/标签表。

## 推荐的本地模型资产

使用带 Git LFS 的当前源码检出：

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e ".[model,classifier]"
git rev-parse HEAD
```

DGN 检查点和分类器包随后位于 `assets/models/`。请记录 `git rev-parse HEAD` 输出的提交哈希，以便以后识别代码和模型检出。也可通过显式 CLI/API 路径或 `HEMISPEC_DGN_MODEL_ROOT`、`HEMISPEC_CLASSIFIER_MODEL_DIR` 选择其他经批准的本地包。

## 当前缓存下载边界

当前 `main` 可以把缺失的 DGN 检查点下载到每用户缓存；文件来自仓库 `main` 分支通过 Git LFS 跟踪的内容。这些下载使用 GitHub media 端点，并非归档 `v0.1.0` GitHub Release 的资产。当前分类器缓存下载并不完整，因为所需的 `feature_names.csv` media URL 返回 HTTP 404；请改用 Git-LFS 源码检出中的分类器文件，或显式指定本地分类器目录。设置 `HEMISPEC_MODEL_CACHE` 时，下载的 DGN 文件保存在该目录，否则使用平台对应的用户缓存。

归档 `v0.1.0` wheel 不包含当前模型下载器。PyPI 项目尚未公开，因此 `pip install hemispec-toolkit` 不是当前安装命令。

## ROI 导出的 atlas 文件

ROI 导出是可选功能，需要：

1. 与 HemiSpec 图具有相同网格和 affine 的分区 atlas NIfTI；
2. 与该 atlas 兼容的标签表。

仓库仅包含 atlas manifest/template 和放置说明。Glasser NIfTI 与标签表不在公开源码分支中分发，因为必须先记录来源、许可证、校验和与再分发批准。

将经批准的本地资产放置于：

```text
assets/atlases/glasser/MNI_Glasser_HCP_v1.0_1p5mm.nii.gz
assets/atlases/glasser/Glasser_label_index_mapping.xlsx
```

或配置显式路径：

```bash
export HEMISPEC_GLASSER_ATLAS=/approved/path/atlas.nii.gz
export HEMISPEC_GLASSER_LABEL_TABLE=/approved/path/labels.xlsx
```

没有 atlas 时，可使用 `--no-roi-table` 仅生成体素级 ANS/RNS 图。

## 不分发的内容

公开分支不能包含原始或受试者级 MRI、研究生成结果、未发表队列结果、稿件草图，或缺少再分发批准的 atlas 文件。

## 归因

跨半球 DGN 与 ANS/RNS 框架源自 Wang 等人（2024）。使用 Glasser/HCP-MMP atlas 时，还应引用 Glasser 等人（2016），并另行记录派生 MNI NIfTI 转换版的来源；详见[引用](citation.md)。模型和 atlas 包还需要各自的来源、校验和、兼容性和许可证记录。
