# HemiSpec GUI 使用说明

HemiSpec GUI 是一个紧凑的标准流程启动器。它面向普通用户：用户提供预处理后的 GM maps，HemiSpec 使用已配置的模型流程生成 ANS/RNS 输出。GUI 不提供训练功能，也不暴露调试级模型参数。

## 启动方式

源码环境：

```powershell
python -m pip install -e .[gui]
hemispec-gui
```

编译后的 Windows GUI 位于：

```text
dist/hemispec_gui/hemispec_gui.exe
```

注意：这是 onedir 分发形式，不要只移动 `hemispec_gui.exe`，需要保留整个 `dist/hemispec_gui/` 文件夹。

## GUI 暴露的用户决策

当前 GUI 是单页布局，包含五个模块：

1. **Input GM maps**：输入预处理后的 GM map glob，例如 `derivatives/*_GM_masked.nii.gz`。
2. **Output workspace**：输出目录。流程会创建 `recon/`、`metrics/`、`subject_maps/`、`subject_hemi_maps/`、`tables/`。
3. **Optional ROI table**：可选 ROI 表格导出。默认使用本地配置的 Glasser atlas，也可以选择自定义 atlas 和 label table。
4. **Optional validation**：可选 hemisphere-classifier validation 和 TRT reliability。classifier validation 需要 ROI table。
5. **Run HemiSpec**：运行流程，查看日志，打开输出目录，复制等价 CLI 命令。

## GUI 不暴露的参数

以下参数由 HemiSpec 默认配置封装，普通用户不需要选择：

- DGN model root
- device / CPU / CUDA
- ANS/RNS threshold 和 epsilon
- 文件后缀和 session regex
- classifier bundle 路径
- ROI statistic
- TRT 详细参数

高级用户应通过 CLI 或 Python API 控制这些参数。

## 输出

标准 workflow 的主要输出是 voxel-wise 和 subject-level ANS/RNS maps：

```text
subject_maps/<subject>_ANS.nii.gz
subject_maps/<subject>_RNS.nii.gz
subject_hemi_maps/<subject>_ANS.L.nii.gz
subject_hemi_maps/<subject>_ANS.R.nii.gz
subject_hemi_maps/<subject>_RNS.L.nii.gz
subject_hemi_maps/<subject>_RNS.R.nii.gz
tables/subject_metric_summary.csv
```

如果启用 ROI table 且 atlas 可用，会额外生成：

```text
tables/roi_features_bilateral.csv
tables/roi_features_bilateral_wide.csv
```

如果启用 classifier 或 TRT，会在对应子目录生成 validation summary。

## CLI 等价命令

GUI 中的 **Copy CLI Command** 会复制对应的 `hemispec workflow` 命令。建议在论文分析或批量任务中保存该命令，以保证可复现。

## 常见问题

- 如果 DGN 模型缺失，检查 `HEMISPEC_DGN_MODEL_ROOT` 或本地 `assets/models/dgn/`。
- 如果 ROI table 未生成，检查 atlas NIfTI 是否存在，或关闭 ROI table 只保留 voxel-wise ANS/RNS 输出。
- 如果 classifier validation 失败，先确认 ROI table 已启用，并且 classifier bundle 已配置。
- 如果需要集群批量运行，优先使用 CLI，不建议用 GUI 批量处理大队列。
