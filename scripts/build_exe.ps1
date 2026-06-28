$ErrorActionPreference = "Stop"

$Python = if ($env:PYTHON) { $env:PYTHON } else { "python" }

& $Python -m pip install -e .[dev]
& $Python -m PyInstaller --clean --noconfirm hemispec.spec
& $Python -m PyInstaller --clean --noconfirm hemispec_gui.spec
