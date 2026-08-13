from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


MODEL_HEADING = re.compile(r"^## Model M\d+ — (?P<name>[^\n]+)", re.MULTILINE)
IDENTITY_SECTION = re.compile(
    r"^### Identity\s*\n\s*(?P<identity>value|entity)\s*$", re.MULTILINE
)


def _state1_identities(project: Path) -> tuple[dict[str, str], list[dict[str, str]]]:
    identities: dict[str, str] = {}
    findings: list[dict[str, str]] = []
    for path in sorted(project.glob("01_models*.md")):
        text = path.read_text(encoding="utf-8")
        headings = list(MODEL_HEADING.finditer(text))
        for index, heading in enumerate(headings):
            name = heading.group("name").strip()
            end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
            match = IDENTITY_SECTION.search(text, heading.end(), end)
            if not match:
                continue
            identity = match.group("identity")
            if name in identities:
                findings.append({
                    "code": "duplicate_state1_model",
                    "model": name,
                    "message": f"{name} has more than one canonical State 1 model record.",
                })
            identities[name] = identity
    return identities, findings


def _closure_identities(project: Path) -> tuple[dict[str, str], list[dict[str, str]]]:
    identities: dict[str, str] = {}
    findings: list[dict[str, str]] = []
    for path in sorted(project.glob("60_model_closure_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for name, model in payload.get("models", {}).items():
            if not isinstance(model, dict) or model.get("kind") == "interface":
                continue
            identity = model.get("identity")
            if name in identities:
                findings.append({
                    "code": "duplicate_closure_model",
                    "model": name,
                    "message": f"{name} appears in more than one model-closure file.",
                })
            identities[name] = identity
    return identities, findings


def lint(project: Path) -> dict[str, Any]:
    global_spec = json.loads((project / "global_spec.json").read_text(encoding="utf-8"))
    assembled = {
        name: model.get("identity")
        for name, model in global_spec.get("models", {}).items()
        if isinstance(model, dict) and model.get("kind") != "interface"
    }
    state1, findings = _state1_identities(project)
    closure, closure_findings = _closure_identities(project)
    findings.extend(closure_findings)

    for name, identity in sorted(assembled.items()):
        if name not in state1:
            findings.append({
                "code": "missing_state1_model",
                "model": name,
                "message": f"Assembled runtime model {name} has no canonical State 1 model record.",
            })
        elif state1[name] != identity:
            findings.append({
                "code": "state1_identity_mismatch",
                "model": name,
                "message": f"{name}: assembled={identity}, State 1={state1[name]}.",
            })

        if name not in closure:
            findings.append({
                "code": "missing_model_closure",
                "model": name,
                "message": f"Assembled runtime model {name} is absent from model closure.",
            })
        elif closure[name] != identity:
            findings.append({
                "code": "closure_identity_mismatch",
                "model": name,
                "message": f"{name}: assembled={identity}, model closure={closure[name]}.",
            })

    return {
        "summary": {
            "assembled_runtime_models": len(assembled),
            "state1_models": len(state1),
            "closure_models": len(closure),
            "errors": len(findings),
        },
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify assembled runtime model identities against State 1 and model closure."
    )
    parser.add_argument("project", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report = lint(args.project)
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        summary = report["summary"]
        print(
            "Identity closure: "
            f"{summary['assembled_runtime_models']} assembled runtime models, "
            f"{summary['errors']} errors"
        )
        for finding in report["findings"]:
            print(f"ERROR {finding['code']} [{finding['model']}] - {finding['message']}")
    return 1 if report["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
