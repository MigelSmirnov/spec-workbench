"""State 7 port closure: a note routing through a port names its methods, and one
operation has one owner (client_portal b3bfb504: invented repository methods)."""
from __future__ import annotations

import json

from notes_workbench import gate, port_closure

CONTRACTS = {
    "PortalStore.begin": "(self) -> PortalTransaction",
    "PortalTransaction.commit": "(self) -> None",
    "PortalTransaction.audit": "(self) -> AuditRepository",
    "PortalTransaction.staff_access": "(self) -> StaffAccessRepository",
    "StaffAccessRepository.get_staff_by_email": "(self, email: str) -> StaffAccount | None",
    "StaffAccessRepository.insert_staff_account": "(self, account: StaffAccount) -> None",
    "AuditRepository.insert_audit": "(self, record: AuditRecord) -> None",
    "append_audit": "(repository: AuditRepository, intent: AuditIntent) -> AuditRecord",
    "create_staff_account": "(store: PortalStore, email: str) -> StaffAccount",
    "bootstrap": "(port: StaffAccessRepository, email: str) -> None",
}
INTERFACES = {"StaffAccessRepository", "AuditRepository"}
ROUTE = ("create_staff_account: [DEPENDENCY_BOUNDARY] MUST reach account persistence only through "
         "the staff_access repository of that transaction")


def _notes(*lines: str) -> list[dict]:
    out = []
    for number, line in enumerate(lines, start=1):
        scope, rest = line.split(": ", 1)
        out.append({"line": number, "scope": scope, "class": rest[1:rest.index("]")],
                    "text": rest[rest.index("]") + 2:]})
    return out


def _unnamed(*lines: str) -> list[tuple[str, str]]:
    return [(f["scope"], f["port"]) for f in port_closure.port_methods_unnamed(_notes(*lines), CONTRACTS, INTERFACES)]


def test_routing_through_an_accessor_without_a_method_blocks():
    findings = port_closure.port_methods_unnamed(_notes(ROUTE + "."), CONTRACTS, INTERFACES)
    assert [(f["code"], f["scope"], f["port"]) for f in findings] == [
        ("port_methods_unnamed", "create_staff_account", "StaffAccessRepository")]
    assert "get_staff_by_email, insert_staff_account" in findings[0]["hint"]
    assert "'<method> of the staff_access repository'" in findings[0]["hint"]


def test_a_method_named_in_any_note_of_the_scope_closes_it():
    assert _unnamed(ROUTE + ".", "create_staff_account: [BEHAVIOR] MUST read the account by calling "
                    "get_staff_by_email of the staff_access repository.") == []
    assert _unnamed(ROUTE + " and call StaffAccessRepository.insert_staff_account once.") == []
    # the interface by name with a bare method of it: the interface is imported, its operations listed
    assert _unnamed("create_staff_account: [BEHAVIOR] MUST read through StaffAccessRepository: "
                    "get_staff_by_email answers the account.") == []


def test_delegation_to_a_callable_that_takes_the_port_closes_it():
    assert _unnamed("create_staff_account: [ORCHESTRATION] MUST append its audit only through the audit "
                    "repository of that transaction, with the imported append_audit.") == []
    assert _unnamed("create_staff_account: [ORCHESTRATION] MUST append its audit only through the audit "
                    "repository of that transaction.") == [("create_staff_account", "AuditRepository")]


def test_a_port_the_scope_takes_as_a_parameter_and_the_port_itself_are_exempt():
    # an imported interface's operations are listed in the prompt
    assert _unnamed("bootstrap: [DEPENDENCY_BOUNDARY] MUST persist only through StaffAccessRepository.") == []
    assert _unnamed("StaffAccessRepository.insert_staff_account: [SCHEMA_CONSTRAINT] MUST write only "
                    "through the staff_access repository of the caller.") == []


def test_duplicate_surface_blocks_unless_a_decision_names_the_duplicate():
    contracts = {**CONTRACTS,
                 "PortalTransaction.get_staff_by_email": "(self, email: str) -> StaffAccount | None",
                 "PortalTransaction.insert_staff_account": "(self, account: StaffAccount) -> None"}
    findings = port_closure.duplicate_contract_surfaces(contracts, INTERFACES, [])
    assert [(f["code"], f["scope"], f["port"], f["methods"]) for f in findings] == [
        ("duplicate_contract_surface", "PortalTransaction.staff_access", "StaffAccessRepository",
         ["get_staff_by_email", "insert_staff_account"])]
    decision = "### A31 — keep PortalTransaction.get_staff_by_email for the bootstrap reader"
    kept = port_closure.duplicate_contract_surfaces(contracts, INTERFACES, [decision])
    assert [f["methods"] for f in kept] == [["insert_staff_account"]]
    assert port_closure.duplicate_contract_surfaces(CONTRACTS, INTERFACES, []) == []


def test_the_notes_gate_blocks_on_both(tmp_path):
    contracts = {**CONTRACTS, "PortalTransaction.get_staff_by_email": "(self, email: str) -> StaffAccount | None"}
    (tmp_path / "30_modules.md").write_text("## `module:staff`\n", encoding="utf-8")
    (tmp_path / "60_contracts.json").write_text(json.dumps({"contracts": contracts}), encoding="utf-8")
    (tmp_path / "global_spec.json").write_text(json.dumps({
        "models": {name: {"kind": "interface"} for name in INTERFACES}, "contracts": contracts}), encoding="utf-8")
    (tmp_path / "80_notes.md").write_text(ROUTE + ".\n", encoding="utf-8")
    report = gate.coverage(tmp_path)
    codes = [f["code"] for f in report["findings"]]
    assert "port_methods_unnamed" in codes and "duplicate_contract_surface" in codes
    assert all(f["severity"] == "block" for f in report["findings"]
               if f["code"] in {"port_methods_unnamed", "duplicate_contract_surface"})
    assert report["summary"]["handoff_ready"] is False
