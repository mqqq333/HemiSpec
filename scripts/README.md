# Scripts

This folder contains developer and release helper scripts. Runtime logic should not live here; shared behavior belongs under `src/hemispec/`.

- `hemispec.cmd`, `hemispec_entry.py` — local Windows launcher helpers.
- `hemispec_gui_d2l.cmd`, `hemispec_gui_entry.py` — local GUI launcher helpers.
- `build_release.ps1` — wheel, entry-point, PyInstaller, and GUI smoke-test release workflow.
- `build_exe.ps1` — legacy/simple executable build helper.
- `research/` — project-owner research utilities for local experiments; keep inputs and outputs outside git.
