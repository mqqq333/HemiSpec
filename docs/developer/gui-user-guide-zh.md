# HemiSpec GUI 使用说明

HemiSpec GUI 是英文界面的研究工具工作台，用于部署训练好的 DGN 模型、计算 ANS/RNS，并完成 ROI 导出、TRT 信度检验和半球分类验证。GUI 不包含模型训练功能；`train_code/` 只作为开发参考。

## 启动方式

当前 GUI exe 位于：

```text
<local-hemispec-toolkit>\dist\hemispec_gui\hemispec_gui.exe
```

直接双击 `hemispec_gui.exe` 即可打开 GUI。注意不要只移动这个 exe；它需要和同目录下的 `_internal/` 文件夹一起保留。

命令行 exe 是：

```text
<local-hemispec-toolkit>\dist\hemispec.exe
```

这个文件用于 CLI，例如：

```powershell
cd <local-hemispec-toolkit>
.\dist\hemispec.exe workflow --help
```

开发阶段或需要完整 PyTorch/DGN runtime 时，推荐用 d2l 环境启动：

```powershell
scripts\hemispec_gui_d2l.cmd
```

也可以从源码启动：

```powershell
$env:PYTHONPATH='src'
<torch-env-python> -m hemispec.gui
```

## 输入预处理要求

DGN 推理和 ANS/RNS 计算前，应先使用项目提供的预处理脚本：

```text
src/hemispec/resources/preprocess/process_single_subject_GM_v2_reorient.sh
```

GUI 的输入应是预处理后的 GM map：

```text
*_GM_masked.nii.gz
```

示例输入位于：

```text
examples/input_sample/
```

## 页面结构

GUI 左侧导航包含：

```text
Full Workflow           双向 DGN + 双侧 ANS/RNS + ROI + classifier + optional TRT
Single Direction        单方向 DGN + ANS/RNS，用于调试或单侧分析
DGN Inference           只运行 DGN 半球重建
Compute ANS/RNS         已有 GM 与 reconstructed GM 时单独计算 ANS/RNS
TRT Reliability         对 ANS/RNS map 做 test-retest 信度检验
Hemisphere Classifier   用保存好的 ROI-level 半球分类模型验证分类准确率
Structural Specificity  做 within-subject vs between-subject 结构特异性检验
```

底部 `Run log` 会显示运行进度、输出路径和错误 traceback。

## Generate ANS/RNS?? Full Workflow?

???????????????? GM ????GUI ??????? HemiSpec DGN ???????????

```text
L_to_R = left hemisphere -> generated right hemisphere
R_to_L = right hemisphere -> generated left hemisphere
```

???? voxel-wise / subject-level ANS ? RNS???????????????????? ROI ???

```text
subject_maps/<subject>_ANS.nii.gz
subject_maps/<subject>_RNS.nii.gz
subject_hemi_maps/<subject>_ANS.L.nii.gz
subject_hemi_maps/<subject>_ANS.R.nii.gz
subject_hemi_maps/<subject>_RNS.L.nii.gz
subject_hemi_maps/<subject>_RNS.R.nii.gz
tables/subject_metric_summary.csv
```

ROI table ?????????? ROI table??????? Glasser atlas????????? atlas/label table ????? parcellation ? ROI-wise ?????????? ROI ????????? ROI table????? voxel-wise ANS/RNS map?

?????

```text
Preprocessed GM glob        ?? GM ?????
Output workspace            ????
Also export ROI table       ????? ROI-wise CSV
Optional ROI atlas NIfTI    ????? Glasser atlas???????? atlas
Optional ROI label table    ????? Glasser label table
Run hemisphere classifier   ????? ROI table
Run TRT reliability         ?????????????
```

?? root?checkpoint?device?GM threshold?RNS epsilon?suffix?regex ??????????????????????????????? CLI ? advanced/debug ?????

????? `docs/developer/outputs-zh.md`?

## Single Direction

用于只跑一个方向：

```text
L_to_R -> 生成右半球
R_to_L -> 生成左半球
```

单方向输出适合调试模型、检查 checkpoint、或者复现实验中的单侧 TRT。正式部署分析建议优先使用 `Full Workflow`。

## Compute ANS/RNS

当你已经有 actual GM 和 DGN-reconstructed GM 时，可以直接用此页计算：

```text
ANS = abs(GM - recon)
RNS = abs(GM - recon) / (abs(GM) + abs(recon) + eps)
```

导出路线：

```text
voxel-wise  保存 group/subject NIfTI maps
ROI-wise    用 atlas 汇总为 ROI CSV
```

## TRT Reliability

输入应是每个被试两个 session/run 的 ANS/RNS map，例如：

```text
sub-MSC01_run-01_ANS.nii.gz
sub-MSC01_run-02_ANS.nii.gz
sub-MSC01_run-01_RNS.nii.gz
sub-MSC01_run-02_RNS.nii.gz
```

默认解析规则：

```text
File regex: (sub-MSC\d+).*?(run-\d+)
Session A:  run-01
Session B:  run-02
```

对于 `Full Workflow` 输出，TRT 通常使用 `subject_maps/`，并选择 L/R 两个半球。对于单方向输出，可使用：

```text
Hemispheres / ROIs: auto
DGN direction:      auto
```

## Hemisphere Classifier

半球分类页面加载已经保存好的 sklearn/joblib 模型，不重新训练。当前模型目录：

```text
assets/models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models/
```

可以输入两种形式：

```text
1. 已有 ROI-wise ANS/RNS CSV
2. ANS/RNS maps + atlas，由 GUI 先生成 ROI features 再分类
```

分类器会把左半球和右半球 ROI-wise feature 输入模型，并输出 prediction、probability、accuracy 和 confusion matrix。

## 常见问题

如果 GUI 提示 PyTorch 不可用，说明当前启动方式不适合跑 DGN。用：

```powershell
scripts\hemispec_gui_d2l.cmd
```

如果文件名不是 MSC 格式，需要修改 `TRT file regex` 或 `File regex`，推荐使用 named groups：

```text
(?P<subject>sub-[0-9]+).*?(?P<session>ses-[0-9]+)
```

如果 ROI 导出失败，优先检查：

```text
1. atlas 与 ANS/RNS map 的 shape 是否一致
2. affine 是否一致
3. label table 是否能被 pandas 读取
4. 输入 map 是否包含有限值而不是全 NaN
```
