from __future__ import annotations

import sys
from pathlib import Path

EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXPERIMENT_ROOT.parents[1]
for entry in (REPO_ROOT / "tools", REPO_ROOT, EXPERIMENT_ROOT / "tools"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))
