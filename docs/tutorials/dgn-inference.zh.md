# DGN 推理

本教程展示如何将已发布的 HemiSpec DGN 模型包应用于预处理灰质图。

## 安装

从 PyPI 运行启用模型的安装时，包含 model 额外依赖，并可选择预下载已发布检查点：

```bash
python -m pip install "hemispec-toolkit[model]"
hemispec models --install
```

源码开发时，请使用 Git LFS 克隆，并运行 `python -m pip install -e .[model]`。

## 输入

- 预处理的 `*_GM_masked.nii.gz` 文件。
- 包含权重、模型方向、预处理假设和版本元数据的 HemiSpec 模型包。

## 输出

- 重建的半球图。
- 源半球和目标半球记录。
- 包含模型版本、命令、参数和输出路径的运行清单。

## 当前状态

默认已发布模型包可通过 Git LFS 源码检出或 PyPI 首次运行缓存下载获得。发布任何额外训练权重前，需先批准发布政策、出处、校验和和许可证说明。
