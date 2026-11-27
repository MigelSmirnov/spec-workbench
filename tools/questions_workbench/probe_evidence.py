"""Post-probe reading for the author, using the saved module prompt only."""
import hashlib
import json
from pathlib import Path

from . import judge

GUIDANCE = ("Before editing, compare the finding with the saved generator prompt and the module's "
            "earlier answers. A decision found only in a design document may still be missing "
            "from the consumer prompt. Historical answers require the same issue and applicable "
            "evidence; the author decides that. A probe does not reopen a round.")


def report(case: Path, probe: Path, module: str) -> dict:
    summary = json.loads((probe / "summary.json").read_text(encoding="utf-8"))
    if summary.get("schema_version") != "spec_workbench_question_probe.v1" or summary.get("state") != 7:
        raise ValueError("Expected a saved State 7 probe directory")
    if summary.get("case_name") and summary["case_name"] != case.resolve().name:
        raise ValueError(f"This probe belongs to {summary['case_name']}; choose the matching case")
    if Path(module).name != module or module not in summary["modules"]:
        raise ValueError(f"Choose a module in the probe: {', '.join(sorted(summary['modules']))}")
    path = probe / "prompts" / f"{module}.txt"
    prompt = path.read_text(encoding="utf-8")
    if hashlib.sha256(prompt.encode("utf-8")).hexdigest() != summary["units"].get(module):
        raise ValueError(f"The saved prompt for {module} differs from the probe summary")
    past = []
    for source in sorted((case / "questions/state7").glob("round-*/summary.json")):
        record = json.loads(source.read_text(encoding="utf-8"))
        for topic in record.get("topics", []):
            if module not in (topic.get("units") or []):
                continue
            verdict = topic.get("judgement") or {}
            if not verdict.get("verified") or verdict.get("blocking"):
                continue
            answer = verdict.get("precedent") or verdict
            if answer.get("kind") != "answered" or not answer.get("quotes"):
                continue
            past.append({"round": record["round"], "record": str(source.relative_to(case)),
                         "topic": topic["topic"], "why": answer.get("why", ""), "quotes": answer["quotes"],
                         "evidence_in_saved_prompt": judge.precedent_holds(answer, prompt)})
    return {"module": module, "prompt": str(path), "guidance": GUIDANCE,
            "probe_topics": [topic for topic in summary["topics"] if module in (topic.get("units") or [])],
            "historical_answers": past}
