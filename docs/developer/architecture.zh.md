# 架构说明

HemiSpec Toolkit 遵循分层架构，使 CLI、GUI 和未来的 notebook 都调用同一套经过测试的核心逻辑。

```text
用户输入 / 文件
      |
      v
CLI（hemispec）或 GUI（hemispec-gui）
      |
      v
公开 API 和工作流编排（api.py、workflow.py）
      |
      +--> DGN 推理（dgn_inference.py、dgn_model.py）
      +--> ANS/RNS 计算（compute.py、similarity.py）
      +--> ROI 汇总（roi.py）
      +--> 验证/报告（hemisphere_classifier.py、reports.py、plots.py）
      |
      v
输出：图、ROI 表、汇总和图表
```

## 设计原则

- **单一实现路径**：CLI、GUI 和 Python 用户应共享同一套核心函数。
- **显式资产**：本地 atlas 和模型通过 `paths.py`、环境变量或用户提供的路径发现。
- **小型公开包**：wheel 不应打包私有数据、大型权重或生成输出。
- **稳定命名**：公开代码使用 `hemispec`；ANS/RNS 是指标名称，不是包名。
- **可复现示例**：公开示例使用合成数据，除非输入已明确批准再发行。

## 当前重构边界

当前代码库处于公开发布迁移阶段。最大的接口模块（`cli.py` 和 `gui.py`）目前保持稳定，以避免在打包期间改变运行时行为。未来重构应在相同的公开入口点后面拆分，并在移动行为之前添加测试。
