# v0.1.0 release verification

The HemiSpec v0.1.0 GitHub Release was post-checked on 2026-06-29 after publication: [https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0](https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0).

## Downloaded artifacts

All release assets were downloaded from GitHub into a fresh local verification workspace:

- `HemiSpec-CLI-v0.1.0-win64.exe`
- `HemiSpec-GUI-v0.1.0-win64.zip`
- `hemispec_toolkit-0.1.0-py3-none-any.whl`
- `hemispec_toolkit-0.1.0.tar.gz`
- `HemiSpec-v0.1.0-SHA256SUMS.txt`
- `HemiSpec-v0.1.0-RELEASE_ARTIFACTS.txt`

## Checksum verification

The downloaded artifacts matched `HemiSpec-v0.1.0-SHA256SUMS.txt`:

| Artifact | SHA256 |
| --- | --- |
| `HemiSpec-CLI-v0.1.0-win64.exe` | `451b608fe44ff6f381c08a08fbe4b220cb603bdf74167ec2df91f960c2376981` |
| `HemiSpec-GUI-v0.1.0-win64.zip` | `1b3acc53301a968cd2332fdec1870d220d68f4ec8f77bed9f2195eb830dfeb87` |
| `hemispec_toolkit-0.1.0-py3-none-any.whl` | `3f21eeefdbae99bd7d661dd45e469293107162aa30a339f8e0724c8d8ac4c0f3` |
| `hemispec_toolkit-0.1.0.tar.gz` | `970f8969e79952e4d36ef90218505623950a344f0c5a5338a4ac1fc82e5c7744` |

The two remaining downloaded files, `HemiSpec-v0.1.0-SHA256SUMS.txt` and `HemiSpec-v0.1.0-RELEASE_ARTIFACTS.txt`, are the checksum source and release manifest rather than binary/package payloads in this table.

## Smoke tests

- Downloaded Windows CLI: `HemiSpec-CLI-v0.1.0-win64.exe --help` printed the expected command list.
- Downloaded wheel: installed into a fresh local verification environment and imported from that environment's `site-packages`.

No retained verification evidence supports a claim that the downloaded wheel ran the synthetic quickstart. The `v0.1.0` tag does not contain the current `quickstart.py` module or `hemispec quickstart` command, so that later current-source feature is not part of this historical smoke-test record.

## Known boundary

This historical verification describes only the original `v0.1.0` artifacts and preserves their checksum evidence. Those artifacts do not embed torch, atlas payloads, real MRI inputs, generated outputs, the current synthetic quickstart, or the current model-cache downloader. For current functionality, install from `main`, run `git rev-parse HEAD`, and record that commit hash with the analysis.

## Related pages

- [Release artifacts](../release-artifacts.md)
- [External asset bundles](../reference/asset-bundle.md)
- [Roadmap](roadmap.md)
