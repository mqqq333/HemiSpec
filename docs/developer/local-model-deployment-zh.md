# 本地 DGN 模型部署接入方案

## 总体原则

HemiSpec v1 只部署训练好的 DGN 模型，不包含训练、重新训练或微调流程。

正式发布给外部用户时，软件需要能够加载训练好的本地 DGN 权重。原因很直接：外部用户通常只有预处理后的 GM map，没有 DGN-reconstructed GM map。如果软件不能运行 DGN 推理，就无法从原始 GM 工作流得到 ANS/RNS。

完整发布流程应为：

```text
preprocessed GM -> trained DGN inference -> reconstructed GM -> ANS/RNS -> reliability/specificity validation
```

工程上保持分层：

```text
DGN inference layer: GM -> reconstructed GM
Metric layer: GM + reconstructed GM -> ANS/RNS
Validation layer: ANS/RNS -> reliability/specificity
Interface layer: API -> CLI/PyPI -> GUI
```

`train_code/` 只作为开发参考，用于理解 Generator 架构、checkpoint 格式和半球 crop 规则。API、CLI 和 GUI 不应要求用户运行或安装训练脚本。

## 当前模型资产

已确认方向：

```text
outputs_bi_stable_L = R_to_L = right hemisphere -> generated left hemisphere
outputs_bi_stable_R = L_to_R = left hemisphere  -> generated right hemisphere
```

默认 checkpoint 位置：

```text
assets/models/dgn/outputs_bi_stable_L/ckpts/best_netG_L.pth
assets/models/dgn/outputs_bi_stable_R/ckpts/best_netG_R.pth
```

如果以后改成显式方向命名，当前发现逻辑也支持：

```text
assets/models/dgn/outputs_bi_stable_L/ckpts/best_netG_R2L.pth
assets/models/dgn/outputs_bi_stable_R/ckpts/best_netG_L2R.pth
```

## 命令行入口

列出当前可发现的本地模型：

```bash
hemispec models --root .
```

使用默认模型目录运行推理：

```bash
hemispec infer \
  --direction L_to_R \
  --input-glob "/path/to/GM/*_GM_masked.nii.gz" \
  --out-dir "/path/to/recon" \
  --device auto
```

使用指定 checkpoint 覆盖默认模型发现：

```bash
hemispec infer \
  --checkpoint "/path/to/best_netG_R.pth" \
  --direction L_to_R \
  --input-glob "/path/to/GM/*_GM_masked.nii.gz" \
  --out-dir "/path/to/recon" \
  --device cuda
```

推理完成后接 ANS/RNS 计算：

```bash
hemispec compute \
  --actual-glob "/path/to/GM/*_GM_masked.nii.gz" \
  --predicted-glob "/path/to/recon/*_PRED_LR_full.nii.gz" \
  --out-dir "/path/to/ANS_RNS" \
  --save-subject-maps
```

## GUI 页面要求

正式 GUI 应增加 `DGN inference` 页面，并放在 Compute/TRT/Specificity 之前。

建议输入项：

```text
Bundled DGN root / checkpoint    默认 assets/models/dgn，或单个 checkpoint 覆盖
Input GM glob              预处理后的 *_GM_masked.nii.gz
Output recon directory     reconstructed GM 输出目录
Direction                  L_to_R / R_to_L
Device                     auto / cpu / cuda
Clip recon                 可选，限制输出范围
```

建议运行逻辑：

```text
1. 调用 DGNInferenceConfig 和 run_dgn_inference()
2. 保存 reconstructed GM
3. 可选：自动进入 compute_metrics()
4. 可选：自动进入 validate_specificity()/validate_reliability()
```

GUI 不应直接 import `train_code/`，也不应出现训练按钮。

## 打包策略

建议保留两个发行形态：

```text
basic/dev package
  包含 ANS/RNS compute、TRT、specificity
  适合已有 reconstructed GM 的开发/复现实验场景

model-enabled package/app
  包含 PyTorch 和 trained DGN inference
  适合外部用户从预处理 GM 开始跑完整流程
```

PyTorch/CUDA 和模型权重会显著增加体积，因此模型版更适合 onedir/folder distribution：

```text
HemiSpec_Model_App/
  hemispec_gui.exe
  _internal/
  models/
  configs/
  examples/
  docs/
```

## 仍需确认

```text
1. 公共发布是否允许随包分发模型权重，还是只能从本地/私有目录加载
2. GUI v1 优先支持 Windows 本地推理、Linux/HPC CLI，还是 Windows GUI 控制远端 Linux 推理
3. reconstructed GM 最终文件命名是否继续兼容 *_PRED_LR_full.nii.gz
4. 是否需要同时输出 direction-specific 和 bilateral reconstructed volumes
```
