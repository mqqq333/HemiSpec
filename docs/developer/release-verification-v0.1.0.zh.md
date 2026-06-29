# v0.1.0 发布验证

HemiSpec v0.1.0 GitHub Release 于 2026-06-29 发布后进行了事后检查：[https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0](https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0)。

## 已下载产物

所有发布资产已从 GitHub 下载到全新本地验证工作区：

- `HemiSpec-CLI-v0.1.0-win64.exe`
- `HemiSpec-GUI-v0.1.0-win64.zip`
- `hemispec_toolkit-0.1.0-py3-none-any.whl`
- `hemispec_toolkit-0.1.0.tar.gz`
- `HemiSpec-v0.1.0-SHA256SUMS.txt`
- `HemiSpec-v0.1.0-RELEASE_ARTIFACTS.txt`

## 校验和验证

下载的产物与 `HemiSpec-v0.1.0-SHA256SUMS.txt` 匹配：

| 产物 | SHA256 |
| --- | --- |
| `HemiSpec-CLI-v0.1.0-win64.exe` | `451b608fe44ff6f381c08a08fbe4b220cb603bdf74167ec2df91f960c2376981` |
| `HemiSpec-GUI-v0.1.0-win64.zip` | `1b3acc53301a968cd2332fdec1870d220d68f4ec8f77bed9f2195eb830dfeb87` |
| `hemispec_toolkit-0.1.0-py3-none-any.whl` | `3f21eeefdbae99bd7d661dd45e469293107162aa30a339f8e0724c8d8ac4c0f3` |
| `hemispec_toolkit-0.1.0.tar.gz` | `970f8969e79952e4d36ef90218505623950a344f0c5a5338a4ac1fc82e5c7744` |

## 冒烟测试

- 下载的 Windows CLI：`HemiSpec-CLI-v0.1.0-win64.exe --help` 打印了预期命令列表。
- 下载的 wheel：安装到全新本地验证环境并从该环境的 `site-packages` 导入。
- 公开安全的合成快速入门：从下载的 wheel 成功运行，生成了 ANS/RNS 组图、受试者图、coverage/validN 图和 `toy_roi_summary.csv`。

## 已知边界

本历史验证描述原始 v0.1.0 产物。这些编译产物不嵌入 torch、atlas 有效载荷、真实 MRI 输入或生成输出。当前 main 分支代码通过 Git LFS 和首次运行用户缓存下载添加了已发布 DGN/分类器模型发现；使用更新版本的 wheel/构建来获取该行为。

## 相关页面

- [发布产物](../release-artifacts.md)
- [外部资产包](../reference/asset-bundle.md)
- [路线图](roadmap.md)
