from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"

# Keep tests bound to this unified HemiSpec checkout even if an older editable
# ANSRNS-Toolkit/HemiSpec install is present earlier on the user's environment.
sys.path.insert(0, str(SRC_ROOT))
