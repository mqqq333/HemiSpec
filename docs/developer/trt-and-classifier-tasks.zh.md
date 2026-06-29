# TRT 与分类器任务

本说明记录运行时任务，不发布稿件特定的结果值。

## TRT 可靠性

`hemispec trt` 从配对 ANS/RNS 图中估计测试-重测可靠性。该命令写入相似度矩阵、受试者内汇总、汇总图和 `validation_summary.csv`。

```bash
hemispec trt \
  --maps-dir "/path/to/workflow/intermediate/combined_maps" \
  --out-dir "/path/to/workflow/validation/trt" \
  --kinds ANS,RNS \
  --hemis L,R
```

公开发布前，本文档中只使用已批准/合成的示例。不要在此发布私有队列大小、精确 p 值或仅供稿件使用的汇总统计。

## 半球分类器验证

`hemispec hemi-classify` 加载已保存的 sklearn/joblib 分类器产物并将其应用于 ROI 级 ANS/RNS 特征。训练不是产品功能。

```bash
hemispec hemi-classify \
  --maps-dir "/path/to/workflow/voxel_maps" \
  --roi-csv "/path/to/workflow/tables/roi_features_bilateral.csv" \
  --classifier-model-dir "/path/to/classifier_bundle" \
  --out-dir "/path/to/workflow/validation/hemi_classify"
```

支持的运行时模式：

```text
single
paired_residual
```

仅通过已批准的模型卡或稿件安全发布说明发布模型性能。模型卡应包含训练/验证出处、特征变换、软件版本、校验和和引用边界。
