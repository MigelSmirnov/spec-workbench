"""Build packet/BUNDLE.md: the packet, the proposed patch, and every cited
passage verbatim. This is exactly what the hand-over check receives.

    python experiments/registry-state2-authoring/make_bundle.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "model"))
from sources import Q  # noqa: E402

packet = (HERE / "packet" / "PACKET.md").read_text(encoding="utf-8")
patch = (HERE / "patch" / "option_A.patch").read_text(encoding="utf-8")
keys = list(dict.fromkeys(re.findall(r"\[q:([A-Za-z0-9_.\-]+)\]", packet)))
out = [packet, "", "## The proposed patch, verbatim", "", "```diff", patch.rstrip(), "```", "",
       "## Appendix — cited passages, verbatim", ""]
for k in keys:
    sha, path, text = Q[k]
    where = f"commit message of {sha}" if path == "-" else f"{sha}:{path}"
    out.append(f"- **[q:{k}]** `{where}`\n\n  > {' '.join(text.split())}\n")
(HERE / "packet" / "BUNDLE.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"{len(keys)} passages; {len(' '.join(out).split())} words")
