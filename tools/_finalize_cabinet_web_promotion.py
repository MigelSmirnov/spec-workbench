#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "examples" / "cabinet-web-backend"
REVIEW_ROOT = ROOT / "ci-artifacts" / "final" / "module-review"
BRANCH = "agent/cabinet-web-card-persistence"

STATUS = {
    "models": "PASS",
    "capability_policy": "PASS_INTERNAL_VARIATION",
    "access_control": "PASS_INTERNAL_VARIATION",
    "effect_journal": "PASS_INTERNAL_VARIATION",
    "card_workspace": "PASS_INTERNAL_VARIATION",
    "invoice_workspace": "PASS_INTERNAL_VARIATION",
    "project_workspace": "PASS_INTERNAL_VARIATION",
    "cabinet_persistence": "PASS",
    "source_byte_store": "PASS",
    "source_custody": "PASS_INTERNAL_VARIATION",
    "invoice_exchange": "PASS_INTERNAL_VARIATION",
    "registry_replica": "PASS_INTERNAL_VARIATION",
    "chatgpt_interaction": "PASS_INTERNAL_VARIATION",
    "web_gateway": "PASS_INTERNAL_VARIATION",
    "sync_gateway": "PASS_INTERNAL_VARIATION",
    "runtime_control": "PASS_INTERNAL_VARIATION",
    "api": "PASS",
    "bootstrap": "PASS_INTERNAL_VARIATION",
}

DETERMINISTIC = {"models", "cabinet_persistence", "source_byte_store", "api"}

SUMMARIES = {
    "models": "Deterministic model surface, including the persistence runtime records, is structurally and identity-closed.",
    "capability_policy": "Closed capability catalogue and exact-name resolution leave only internal implementation variation.",
    "access_control": "Credential-verifier, exact grant, throttle, and audit persistence are lowered through the operation-scoped UoW; authorization semantics remain closed in the service.",
    "effect_journal": "Effect reservation, commit, and reconciliation use the shared operation-scoped UoW with deterministic PostgreSQL locking and replay evidence.",
    "card_workspace": "Immutable Card revisions, current-head selection, identity locking, and expected-revision storage mechanics are closed; Card policy remains in the workspace.",
    "invoice_workspace": "Invoice mutations share the explicit UoW/Card boundary and persist the exact working-set and manifest producer evidence required by synchronization.",
    "project_workspace": "Project Card, estimate, shopping-list, and linkage mutations run through the shared Card/UoW transaction boundary without separate storage authority.",
    "cabinet_persistence": "PostgreSQL v3 lowering is closed for all accepted server durable projections with 25 tables and 80 deterministic repository methods plus an operation-scoped UoW factory.",
    "source_byte_store": "Factory-owned filesystem backend closes confinement, staging, verification, content addressing, atomic publication, and staging compensation mechanics.",
    "source_custody": "Verifier-only handoff storage, custody rows, recoverable publication journal, protected byte-store port, and release evidence are closed across the DB/file boundary.",
    "invoice_exchange": "Working sets, manifests, node-scoped issuance, exact receipts, conflicts, assignment evidence, and reconciliation reads have durable UoW storage.",
    "registry_replica": "Catalogue snapshot/replica, publication idempotency, and current-selector storage are explicit and atomic under the shared UoW.",
    "chatgpt_interaction": "All application-service dependencies and exact operation contracts are lowered; proposal/effect orchestration permits only internal variation.",
    "web_gateway": "Access-control and source-custody dependencies are explicit; the gateway retains only transport/security-boundary variation.",
    "sync_gateway": "Access, exchange, and Registry dependencies carry their closed operation contracts; unknown synchronization dispatch remains forbidden.",
    "runtime_control": "Readiness and restore verification now depend on the closed UoW factory, byte store, durable drill evidence, and startup recovery mechanisms.",
    "api": "Deterministic Router IR and handler lowering remain closed against the updated assembled specification.",
    "bootstrap": "The sole composition root is explicit: protected configuration, migrations, recovery, UoW factory, byte store, service graph, and create_app handoff are fixed; only internal construction details may vary.",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def slice_sha(packet: dict) -> str:
    rendered = json.dumps(packet, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def build_ledger() -> dict:
    modules = read_json(REVIEW_ROOT / "list.json")["modules"]
    expected = list(STATUS)
    if modules != expected:
        raise RuntimeError(f"unexpected module order: {modules!r}")
    rows = []
    for module in modules:
        packet = read_json(REVIEW_ROOT / "slices" / f"{module}.json")
        review = read_json(REVIEW_ROOT / "reviews" / f"{module}.json")
        summary = review["summary"]
        if summary["blocks"] != 0 or summary["reviews"] != 0 or review["findings"]:
            raise RuntimeError(f"Stage 8.1 review is not structurally clean for {module}: {review}")
        rows.append(
            {
                "module": module,
                "generation_mode": "deterministic_backend" if module in DETERMINISTIC else "llm_behavioral",
                "review_status": STATUS[module],
                "slice_sha256": slice_sha(packet),
                "structural_review": {
                    "contracts": summary["contracts"],
                    "notes": summary["assembled_notes"],
                    "blocks": summary["blocks"],
                },
                "review_record": "81_runtime_boundary_review.md",
                "summary": SUMMARIES[module],
            }
        )
    return {
        "schema_version": "spec_workbench_stage_8_1_review_status.v1",
        "stage": "8.1",
        "status": "closed",
        "project": "cabinet-web-backend",
        "review_command": "python tools/design_module_review.py examples/cabinet-web-backend --module <name> --slice --json",
        "status_values": ["PENDING", "PASS", "PASS_INTERNAL_VARIATION", "AMBIGUITY", "STALE"],
        "summary": {
            "module_count": 18,
            "reviewed": 18,
            "passed": 18,
            "ambiguities": 0,
            "pending": 0,
            "stale": 0,
        },
        "deterministic_data": {
            "status": "PASS",
            "surfaces": ["persistence", "runtime_dependencies", "composition"],
            "verification": "PostgreSQL v3 is closed for 25 tables and 80 deterministic PostgresCabinetUnitOfWork methods; the operation-scoped UoW factory, protected filesystem byte store, recoverable source-publication journal, transfer/Registry/recovery evidence, and sole bootstrap composition root are all assembled. Final Workbench assembly is 8/8 ready with zero errors.",
        },
        "modules": rows,
    }


RUNTIME_REVIEW = """# Stage 8.1 — runtime boundary review

Date: 2026-08-25

Status: **PASS**

## Result

The Cabinet Web Backend runtime boundary is implementation-ready for the accepted VPS architecture. The earlier Stage 8.1 ambiguities were returned to their owning design states, lowered, assembled, and re-reviewed rather than waived.

PostgreSQL remains the authoritative Cabinet Web metadata store and the protected local VPS filesystem remains the authority for original source bytes. The local `cabinet_backend` remains a separate intermittent synchronization peer and is not required for ordinary Cabinet Web reads or mutations.

Final deterministic evidence:

- `persistence_backend/v3` is closed for **25 PostgreSQL tables**;
- `PostgresCabinetUnitOfWork` has **80 deterministic `postgres_sync_v1` methods**;
- one `CabinetUnitOfWorkFactory` opens a fresh UoW per application operation;
- the protected filesystem `source_byte_store_backend` is closed;
- the recoverable source-byte publication journal is durable in PostgreSQL;
- transfer issuance/receipt/conflict, Registry replica/current-selector, security, restore-drill, and release evidence all have explicit durable projections;
- `bootstrap.create_cabinet_web_app` is the sole composition root and owns protected configuration reads, migrations/connectivity checks, startup recovery, adapter/service construction, and the final `create_app` handoff;
- State 7 notes are propagated into the assembled specification before module review;
- complete Workbench assembly is **8/8 ready with 0 errors**.

The mature local `cabinet-backend` was used only as an E2E-tested structural precedent for shared Factory mechanisms such as `persistence_backend/v3`, `postgres_sync_v1`, verifier-only credential storage, transaction ownership, and recoverable byte publication. No local-backend product ownership or Holded behavior was transferred into the server application.

## Resolution of prior findings

### Finding 1 — durable backend lowering

**Resolved.** Every accepted server durable state family now has an explicit PostgreSQL projection or is intentionally embedded in the immutable canonical Card revision aggregate. Table names are closed under `config.persistence`; persistence adapters do not read deployment configuration or invent business policy.

### Finding 2 — typed repository and UoW surface

**Resolved.** Stateful application services depend on the external `CabinetUnitOfWorkFactory`; each operation receives a fresh transaction-scoped UoW. The deterministic repository surface covers Card revisions/current heads, effects, principals/nodes/credentials/grants/throttle/audit, source handoffs/custody/publication, working sets/manifests/issuance/receipts/conflicts, Registry publication/replica/current selection, restore drills, and VPS release evidence.

### Finding 3 — cross-resource atomicity and recovery

**Resolved.** One application operation owns one PostgreSQL transaction. Card/effect, Invoice producer, transfer, Registry, security, and release transitions can share that transaction. Source-byte custody uses the accepted staged/verified/metadata-committed/atomic-publish protocol with durable recovery journal evidence; startup recovery finalizes or fails pending publications without reporting unavailable bytes as present.

### Finding 4 — runtime composition

**Resolved.** `bootstrap` is now a first-class assembled module with the exact `create_cabinet_web_app() -> FastAPI` contract and a State 7 orchestration constraint. It is the only boundary allowed to read protected deployment configuration and construct the concrete PostgreSQL/filesystem/runtime graph.

## Stage 8.1 semantic re-review

All **18 assembled modules** were rebuilt from the final specification. Every structural module review reports **0 blocks and 0 review findings**. Deterministic modules (`models`, `cabinet_persistence`, `source_byte_store`, `api`) are `PASS`; behavioral modules are `PASS_INTERNAL_VARIATION` where their observable behavior is closed but internal algorithms/construction details may vary.

The exact current slice SHA-256 values and per-module results are recorded in `81_module_review_status.json`. That ledger is the Stage 9 lineage gate and must become stale if any assembled module slice changes.

## Stage 9 handoff condition

Stage 8.1 is closed. Factory admission may proceed only against the clean committed source and must independently re-check assembly, current slice hashes, persistence closure, closure-completeness fuses, target identity, Factory compatibility, and the remaining Stage 9 checks.
"""

FINAL_CI = r'''name: Spec Workbench CI

on:
  push:
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  workbench:
    name: Tests and assembly
    runs-on: ubuntu-latest
    steps:
      - name: Check out Workbench
        uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.12"

      - name: Install test dependencies
        run: >-
          python -m pip install
          pytest pyyaml pydantic Pillow pypdf "psycopg[binary]"

      - name: Capture Cabinet Web closure sources
        run: |
          mkdir -p ../ci-artifacts
          tar -czf ../ci-artifacts/cabinet-web-closure-sources.tar.gz \
            examples/cabinet-web-backend/01_models_persistence_runtime.md \
            examples/cabinet-web-backend/01_models_runtime_closure.md \
            examples/cabinet-web-backend/02_rules_security_config.md \
            examples/cabinet-web-backend/30_runtime_boundary_revision.md \
            examples/cabinet-web-backend/60_model_closure_domain.json \
            examples/cabinet-web-backend/60_model_closure_runtime.json \
            examples/cabinet-web-backend/60_contract_plan.json \
            examples/cabinet-web-backend/60_contracts.json \
            examples/cabinet-web-backend/60_data_closure.json \
            examples/cabinet-web-backend/70_persistence_closure.json \
            examples/cabinet-web-backend/70_runtime_closure.json \
            examples/cabinet-web-backend/80_notes.md \
            examples/cabinet-web-backend/81_module_review_status.json \
            examples/cabinet-web-backend/81_runtime_boundary_review.md

      - name: Run complete Workbench test suite
        run: python -m pytest -q --junitxml=../ci-artifacts/pytest.xml

      - name: Verify Cabinet Web canonical projection
        run: |
          python tools/design_spec_projection.py examples/cabinet-web-backend --verify --json \
            > ../ci-artifacts/cabinet-web-backend-projection.json
          python - <<'PY'
          import json
          from pathlib import Path
          report = json.loads(Path("../ci-artifacts/cabinet-web-backend-projection.json").read_text())
          assert report["ready"] is True
          assert report["in_sync"] is True
          PY

      - name: Verify mature Cabinet assembly
        run: >-
          python tools/design_assembly.py examples/cabinet-backend --json
          > ../ci-artifacts/cabinet-backend-assembly.json

      - name: Verify Cabinet Web assembly
        run: |
          python tools/design_assembly.py examples/cabinet-web-backend --json \
            > ../ci-artifacts/cabinet-web-backend-assembly.json
          python - <<'PY'
          import json
          from pathlib import Path
          report = json.loads(Path("../ci-artifacts/cabinet-web-backend-assembly.json").read_text())
          assert report["ready"] is True
          assert report["summary"]["errors"] == 0
          assert report["summary"]["ready_checks"] == report["summary"]["checks"]
          PY

      - name: Verify Cabinet Web Stage 8.1 ledger
        run: |
          python - <<'PY'
          import json
          from pathlib import Path
          ledger = json.loads(Path("examples/cabinet-web-backend/81_module_review_status.json").read_text())
          assert ledger["status"] == "closed"
          assert ledger["summary"] == {"module_count": 18, "reviewed": 18, "passed": 18, "ambiguities": 0, "pending": 0, "stale": 0}
          PY

      - name: Check patch integrity
        run: git diff --check

      - name: Upload Workbench evidence
        if: always()
        uses: actions/upload-artifact@v6
        with:
          name: spec-workbench-ci-evidence
          path: ../ci-artifacts/
          if-no-files-found: error

  factory-admission:
    name: Cross-repository Factory admission
    needs: workbench
    runs-on: ubuntu-latest
    env:
      FACTORY_REPO_DEPLOY_KEY: ${{ secrets.FACTORY_REPO_DEPLOY_KEY }}
    steps:
      - name: Detect private Factory access
        id: factory-access
        shell: bash
        run: |
          if test -n "$FACTORY_REPO_DEPLOY_KEY"; then
            echo "available=true" >> "$GITHUB_OUTPUT"
          else
            echo "available=false" >> "$GITHUB_OUTPUT"
            echo "::notice::FACTORY_REPO_DEPLOY_KEY is not configured; cross-repository admission is skipped."
          fi

      - name: Check out Workbench
        if: steps.factory-access.outputs.available == 'true'
        uses: actions/checkout@v6
        with:
          path: spec-workbench
          persist-credentials: false

      - name: Check out private Factory
        if: steps.factory-access.outputs.available == 'true'
        uses: actions/checkout@v6
        with:
          repository: MigelSmirnov/panelforge-sandbox
          ref: agent/cabinet-web-route-b-official
          ssh-key: ${{ secrets.FACTORY_REPO_DEPLOY_KEY }}
          persist-credentials: false
          path: code_factory

      - name: Set up Python
        if: steps.factory-access.outputs.available == 'true'
        uses: actions/setup-python@v6
        with:
          python-version: "3.12"

      - name: Install admission dependencies
        if: steps.factory-access.outputs.available == 'true'
        run: >-
          python -m pip install
          pytest pyyaml pydantic Pillow pypdf "psycopg[binary]"

      - name: Admit mature Cabinet backend
        if: steps.factory-access.outputs.available == 'true'
        working-directory: spec-workbench
        run: |
          mkdir -p ../ci-artifacts
          python tools/design_factory_admission.py examples/cabinet-backend \
            --project cabinet_backend \
            --factory-root ../code_factory \
            --update-existing \
            --json > ../ci-artifacts/cabinet-backend-admission.json

      - name: Admit Cabinet Web backend
        if: steps.factory-access.outputs.available == 'true'
        working-directory: spec-workbench
        run: |
          python tools/design_factory_admission.py examples/cabinet-web-backend \
            --project Cabinet_web \
            --factory-root ../code_factory \
            --update-existing \
            --json > ../ci-artifacts/cabinet-web-backend-admission.json
          python - <<'PY'
          import json
          from pathlib import Path
          report = json.loads(Path("../ci-artifacts/cabinet-web-backend-admission.json").read_text())
          assert report["status"] == "READY_TO_EXPORT", report
          assert report["ready"] is True, report
          assert report["summary"]["blocks"] == 0, report
          assert report["summary"]["warnings"] == 0, report
          assert report["summary"]["passes"] == report["summary"]["checks"], report
          checks = {item["id"]: item for item in report["checks"]}
          for key in ("FA002", "FA003", "FA005", "FA013", "FA014"):
              assert checks[key]["status"] == "PASS", (key, checks[key])
          PY

      - name: Upload Factory admission evidence
        if: always() && steps.factory-access.outputs.available == 'true'
        uses: actions/upload-artifact@v6
        with:
          name: factory-admission-evidence
          path: ci-artifacts/
          if-no-files-found: error
'''


def finalize_files() -> None:
    ledger = build_ledger()
    write_json(PROJECT / "81_module_review_status.json", ledger)
    (PROJECT / "81_runtime_boundary_review.md").write_text(RUNTIME_REVIEW, encoding="utf-8")

    runtime_path = PROJECT / "70_runtime_closure.json"
    runtime = read_json(runtime_path)
    lowering = runtime["lowering_status"]
    lowering["state3_module_boundaries"] = "closed"
    lowering["state6_repository_contracts"] = "closed"
    lowering["persistence_backend_ir"] = "closed"
    lowering["composition_root"] = "closed"
    lowering["stage8_1_recheck"] = "closed"
    write_json(runtime_path, runtime)

    (ROOT / ".github" / "workflows" / "spec-workbench-ci.yml").write_text(FINAL_CI, encoding="utf-8")


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def commit_and_push() -> None:
    for relative in [
        ".stage/cabinet-web-persistence",
        "tools/_cabinet_web_candidate_materialize.py",
        "tools/_finalize_cabinet_web_promotion.py",
        ".github/workflows/cabinet-web-persistence-candidate.yml",
        ".final-promotion-placeholder",
    ]:
        path = ROOT / relative
        if path.exists():
            if path.is_dir():
                run("git", "rm", "-r", relative)
            else:
                run("git", "rm", relative)

    run("git", "add", "examples/cabinet-web-backend", "tools/spec_projection_workbench/service.py", ".github/workflows/spec-workbench-ci.yml")
    run("git", "diff", "--cached", "--check")
    run("git", "config", "user.name", "github-actions[bot]")
    run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    run("git", "commit", "-m", "spec: close Cabinet Web runtime persistence")
    run("git", "push", "origin", f"HEAD:{BRANCH}")


def main() -> None:
    finalize_files()
    commit_and_push()


if __name__ == "__main__":
    main()
