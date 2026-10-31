"""Build packet/BUNDLE.md: the packet with every cited passage resolved.

    python experiments/registry-state2-investigation/make_bundle.py

The bundle is what a reader gets without the repository: the packet text,
then each passage it cites, verbatim, with its commit and file.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "model"))
from sources import Q  # noqa: E402

packet = (HERE / "packet" / "PACKET_empty_erasure.md").read_text(encoding="utf-8")
keys = []
for k in re.findall(r"\[q:([A-Za-z0-9_.\-]+)\]", packet):
    if k not in keys:
        keys.append(k)
out = [packet, "", "## Appendix — the cited passages, verbatim", ""]
for k in keys:
    sha, path, text = Q[k]
    out.append(f"- **[q:{k}]** `{sha}:{path}`\n\n  > {' '.join(text.split())}\n")
(HERE / "packet" / "BUNDLE.md").write_text("\n".join(out), encoding="utf-8")
print(f"{len(keys)} passages")
