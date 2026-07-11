# 数据与模型

!!! important "MRI 输入是独立前置条件"
    模型权重和 atlas 文件不会把原始 T1 MRI 自动转换为 DGN 输入。应先为每名受试者准备一张 MNI152 1.5 mm 的 `*_GM_masked.nii.gz`；详见[输入与预处理](input-preprocessing.md)。

HemiSpec 模型工作流使用两个 DGN 生成器检查点、可选半球分类器包，以及用于 ROI 导出的可选 atlas/标签表。

## DGN 与分类器模型包

### Git LFS 源码检出

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e .[model,classifier]
```

### Release wheel 或轻量安装

Python wheel 不嵌入 300MB+ 模型包。安装 v0.1.0 wheel 后，HemiSpec 可将 GitHub Release 中的默认模型下载到每用户缓存：

```bash
python -m pip install "./hemispec_toolkit-0.1.0-py3-none-any.whl[model,classifier]"
hemispec models --install --with-classifier
```

当前 PyPI 项目尚未公开，不能把 `pip install hemispec-toolkit` 作为现行安装说明。

设置 `HEMISPEC_MODEL_CACHE` 时，下载文件存储到指定目录；否则使用平台对应的用户缓存。显式环境变量或 CLI/API 路径可以覆盖默认位置。

## ROI 导出的 atlas 文件

ROI 导出是可选功能，需要：

1. 与 HemiSpec 图具有相同网格和 affine 的分区 atlas NIfTI；
2. 与 atlas 兼容的标签表。

公开源码分支仅保留 atlas manifest/template 和放置说明。Glasser NIfTI 与标签表**不在公开源码分支中分发**，因为必须先记录来源、许可证、校验和与再分发批准。

将已批准的本地资产放置于：

```text
assets/atlases/glasser/MNI_Glasser_HCP_v1.0_1p5mm.nii.gz
assets/atlases/glasser/Glasser_label_index_mapping.xlsx
```

或配置显式路径：

```bash
export HEMISPEC_GLASSER_ATLAS=/approved/path/atlas.nii.gz
export HEMISPEC_GLASSER_LABEL_TABLE=/approved/path/labels.xlsx
```

也可以直接传入自定义 atlas：

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/ \
  --roi-atlas /approved/path/atlas.nii.gz \
  --roi-label-table /approved/path/labels.xlsx
```

没有 atlas 时，可使用 `--no-roi-table` 仅生成体素级 ANS/RNS 图。

## 不分发的内容

公开分支不能包含原始或受试者级 MRI、研究生成结果、未发表队列结果、稿件草图，或缺少再分发批准的 atlas 文件。公开示例应使用合成快速测试。

## 归因

跨半球 DGN 与 ANS/RNS 框架源自 Wang 等人（2024），详见[引用](citation.md)。模型和 atlas 包还需要各自的来源、校验和、兼容性和许可证记录。
