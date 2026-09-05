# CLI 参考

首选公开命令为：

```text
hemispec
```

以下子命令已于 2026-09-05 与当前工具包接口核对。如果工具包源码或包名发生变化，请在公开发布前重新核对。

## 当前子命令

```text
hemispec quickstart      运行公开安全的合成测试
hemispec models          列出或预下载已发布的训练 DGN 模型包
hemispec infer           在预处理 GM 图上运行训练好的 DGN 推理
hemispec compute         从实际和重建 GM 图计算 ANS/RNS 图
hemispec run             运行 DGN 推理然后进行 ANS/RNS 计算
hemispec workflow        运行双向 DGN 并生成 ANS/RNS 输出
hemispec trt             测试-重测可靠性验证
hemispec specificity     结构特异性验证
hemispec hemi-classify   ROI 级半球分类器验证
```

## 命令命名

命令行界面使用 `hemispec`，图形界面使用 `hemispec-gui`。

## 模型资产预取

当前 `main` 可预下载 Git LFS 追踪的 DGN 检查点：

```bash
hemispec models --install
```

如果跳过此步骤，`workflow`、`infer`、`run` 和 GUI 会在首次使用模型时从仓库 `main` 分支的 Git LFS media 下载 DGN 检查点。

CLI 仍支持 `--with-classifier`，但目前不应将其作为可用的安装方法，因为必需的 `feature_names.csv` media URL 返回 HTTP 404。请从本地 Git LFS 检出使用分类器资产，并通过 `--classifier-model-dir` 或 `HEMISPEC_CLASSIFIER_MODEL_DIR` 指定；详见[数据与模型中的已知限制](../data-and-models.md)。

## ROI 输出

ROI 导出目前通过 `compute`、`run` 和 `workflow` 上的选项暴露。对于 `workflow`，ROI 导出是可选的，可用 `--no-roi-table` 跳过；分类器验证通过 `--run-classifier` 选择启用，且需要 ROI 特征。

```text
--roi-atlas
--roi-out-csv
--roi-label-table
--roi-stat
--no-roi-table
--run-classifier
```

目前还没有独立的 `roi` 子命令。

已发布分类器只接受来自兼容 Glasser 1.5 mm atlas 的特征：左侧同源标签为 `1..180`，右侧为 `1001..1180`。自定义 atlas 可用于 ROI 导出，但不能与已发布分类器配合使用。

## 报告

目前还没有独立的 `report` 子命令。报告应被视为计划中的功能，直到实现为止。

ANS/RNS 与跨半球 DGN 框架源自 Wang 等人（2024），详见[引用](../citation.md)。
