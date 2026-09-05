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

其余两个下载文件 `HemiSpec-v0.1.0-SHA256SUMS.txt` 和 `HemiSpec-v0.1.0-RELEASE_ARTIFACTS.txt` 分别是校验和来源与发布清单，不是上表中的二进制/软件包载荷。

## 冒烟测试

- 下载的 Windows CLI：`HemiSpec-CLI-v0.1.0-win64.exe --help` 打印了预期命令列表。
- 下载的 wheel：安装到全新本地验证环境并从该环境的 `site-packages` 导入。

没有保留的验证证据支持“下载的 wheel 运行过合成快速入门”这一说法。`v0.1.0` 标签不包含当前的 `quickstart.py` 模块或 `hemispec quickstart` 命令，因此这一后来加入的当前源码功能不属于本历史冒烟测试记录。

## 已知边界

本历史验证仅描述原始 `v0.1.0` 产物，并保留其校验和证据。这些产物不嵌入 torch、atlas 载荷、真实 MRI 输入、生成输出、当前合成快速入门或当前模型缓存下载器。使用当前功能时，请从 `main` 安装，运行 `git rev-parse HEAD`，并随分析记录该提交哈希。

## 相关页面

- [发布产物](../release-artifacts.md)
- [外部资产包](../reference/asset-bundle.md)
- [路线图](roadmap.md)
