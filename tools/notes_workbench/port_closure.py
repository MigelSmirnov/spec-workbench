"""Port closure of State 7 notes: a note that routes through a port names its methods.

The Factory slicer hands a module only the contracts its notes name. A note
that says an operation reaches persistence "only through the staff_access
repository of that transaction" names the accessor (``PortalTransaction.
staff_access -> StaffAccessRepository``) but no ``StaffAccessRepository``
method, so the generation prompt lists the accessor and none of the port's
operations, and the generator invents them. client_portal spec b3bfb504:
``staff_identity`` called eight StaffAccessRepository methods that do not
exist and ``derived_views`` two BudgetRepository methods; ``viewer_access``,
whose notes say "calling get_viewer_session of the viewer_access repository",
came out right. Two checks:

``port_methods_unnamed``
    A scope whose note routes an operation through a port it does not take as
    a parameter (an imported interface's operations are listed in the prompt) — ``through|via
    [only] the <accessor> repository|port`` with an accessor whose contract
    returns one interface, or ``through|via [the] <Interface>`` — while no note
    of that scope names a method of the interface as an address the flow
    closure resolves (``<method> of the <accessor> repository``,
    ``Interface.method``, ``param.method``), or the interface by name together
    with a method of it (a named interface is imported, and the prompt lists
    an imported interface's operations) and no named callable takes the
    interface as a parameter (``with the imported append_audit into the audit
    repository`` delegates the call to ``append_audit(repository:
    AuditRepository)``).

``duplicate_contract_surface``
    A class whose accessor returns an interface and that also declares, under
    the same names, methods of that interface (``PortalTransaction.
    get_expense_aggregate`` and ``ExpenseRepository.get_expense_aggregate``).
    The generator sees one operation under two owners and picks either, or
    reads the accessor as the repository (``transaction.expenses.get_x``). It
    blocks unless an accepted State 2 decision names the duplicate address
    ``Class.method`` — keeping both is then a decision, not an accident.
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import flow_closure

NAME = r"[A-Za-z_][A-Za-z0-9_]*"
# "through the staff_access repository", "only through that budgets port", "via the audit repository"
THROUGH_ACCESSOR_RE = re.compile(
    rf"\b(?:through|via)\s+(?:only\s+)?(?:the|that|this|its)\s+({NAME})\s+(?:repository|port)\b")
# "through StaffAccessRepository", "via the ExpenseRepository port"
THROUGH_INTERFACE_RE = re.compile(rf"\b(?:through|via)\s+(?:only\s+)?(?:(?:the|that|this|its)\s+)?({NAME})\b")


def _returned_type(signature: Any) -> str:
    returned = str(signature or "").partition("->")[2].strip()
    return returned if flow_closure.TYPE_NAME_RE.match(returned) else ""


def _parameter_types(signature: Any) -> set[str]:
    params = str(signature or "").partition("->")[0]
    return set(re.findall(rf":\s*({NAME})", params))


def interface_methods(interfaces: set[str], signatures: dict[str, Any]) -> dict[str, set[str]]:
    """``{interface: {method}}`` for every interface with at least one method contract."""
    methods: dict[str, set[str]] = defaultdict(set)
    for symbol in signatures:
        owner, _, method = str(symbol).partition(".")
        if owner in interfaces and method and "." not in method and method != "__init__":
            methods[owner].add(method)
    return dict(methods)


def port_methods_unnamed(
    notes: list[dict[str, Any]],
    signatures: dict[str, Any],
    interfaces: set[str],
) -> list[dict[str, Any]]:
    """One finding per (scope, interface) whose notes route through the port and name none of its methods."""
    ports = interface_methods(interfaces, signatures)
    if not ports:
        return []
    accessors: dict[str, set[str]] = defaultdict(set)
    for symbol, signature in signatures.items():
        if "." in str(symbol):
            returned = _returned_type(signature)
            if returned in ports:
                accessors[str(symbol).rsplit(".", 1)[1]].add(returned)
    owners = {str(symbol): "" for symbol in signatures}
    by_scope: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for note in notes:
        by_scope[note["scope"]].append(note)

    findings: list[dict[str, Any]] = []
    for scope, scoped in sorted(by_scope.items()):
        owner_class = scope.split(".", 1)[0] if "." in scope else ""
        routed: dict[str, dict[str, Any]] = {}
        for note in scoped:
            for accessor in THROUGH_ACCESSOR_RE.findall(note["text"]):
                for port in sorted(accessors.get(accessor, ())):
                    routed.setdefault(port, {"note": note, "phrase": f"the {accessor} repository"})
            for name in THROUGH_INTERFACE_RE.findall(note["text"]):
                if name in ports:
                    routed.setdefault(name, {"note": note, "phrase": name})
        # the port's own methods and its implementations do not call into it; a
        # port the scope's contract takes as a parameter is imported, and the
        # prompt lists an imported interface's operations exactly
        given = _parameter_types(signatures.get(scope))
        routed = {port: hit for port, hit in routed.items()
                  if owner_class != port and port not in given and not (owner_class and ports[port] <= {
                      s.split(".", 1)[1] for s in signatures if str(s).startswith(owner_class + ".")})}
        if not routed:
            continue
        lines = [f"{scope}: {note['text']}" for note in scoped]
        named = flow_closure.note_call_edges(lines, owners, signatures).get(
            scope if scope in owners else scope.split(".", 1)[0], set())
        for port, hit in sorted(routed.items()):
            if any(callee.startswith(port + ".") for callee in named):
                continue
            if any(port in _parameter_types(signatures.get(callee)) for callee in named):
                continue  # the call is delegated to a callable that takes the port
            text = "\n".join(note["text"] for note in scoped)
            if re.search(rf"\b{re.escape(port)}\b", text) and any(
                    re.search(rf"\b{re.escape(method)}\b", text) for method in ports[port]):
                continue  # 'through StoreRepository ... load_activation_row': the port and its method by name
            declared = ", ".join(sorted(ports[port]))
            accessor_phrase = hit["phrase"]
            findings.append({
                "severity": "block",
                "code": "port_methods_unnamed",
                "line": hit["note"]["line"],
                "scope": scope,
                "port": port,
                "message": (
                    f"{scope} routes through {accessor_phrase} ({port}) but no note of {scope} names a "
                    f"{port} method: the Factory slicer brings only the contracts a note names, so the "
                    f"prompt lists none of {port}'s operations and the generator invents them."
                ),
                "hint": (
                    "not decided — decide: name each port method the operation calls, as "
                    f"'<method> of {accessor_phrase if accessor_phrase != port else 'the ' + port}' — "
                    f"{port} declares: {declared}; or name the callable that takes the {port} "
                    "(NOTE_GATE.md 'Port access must be named')."
                ),
            })
    return findings


def decision_texts(project: Path) -> list[str]:
    """The authored text of every State 2 decision of the case."""
    import design_index

    texts: list[str] = []
    files: dict[str, list[str]] = {}
    for item in design_index.build_index(project)["items"]:
        if item.get("kind") != "decision":
            continue
        source = item.get("source") or {}
        path = str(source.get("path") or "")
        if path not in files:
            try:
                files[path] = (project / path).read_text(encoding="utf-8").splitlines()
            except OSError:
                files[path] = []
        start, end = int(source.get("start_line") or 1), int(source.get("end_line") or 0)
        texts.append("\n".join(files[path][start - 1:end or None]))
    return texts


def duplicate_contract_surfaces(
    signatures: dict[str, Any],
    interfaces: set[str],
    decisions: list[str],
) -> list[dict[str, Any]]:
    """One finding per (class, interface) whose shared method names no decision keeps."""
    ports = interface_methods(interfaces, signatures)
    methods: dict[str, set[str]] = defaultdict(set)
    for symbol in signatures:
        owner, _, method = str(symbol).partition(".")
        if method and "." not in method and not method.startswith("__"):
            methods[owner].add(method)
    decided = "\n".join(decisions)
    findings: list[dict[str, Any]] = []
    for owner in sorted(methods):
        if owner in ports:
            continue
        for accessor in sorted(methods[owner]):
            port = _returned_type(signatures.get(f"{owner}.{accessor}"))
            if port not in ports:
                continue
            shared = sorted(ports[port] & methods[owner])
            open_ = [m for m in shared if not re.search(rf"\b{re.escape(owner)}\.{re.escape(m)}\b", decided)]
            if not open_:
                continue
            findings.append({
                "severity": "block",
                "code": "duplicate_contract_surface",
                "scope": f"{owner}.{accessor}",
                "port": port,
                "methods": open_,
                "message": (
                    f"{owner} declares {len(open_)} method(s) under the names of {port}, which its accessor "
                    f"{owner}.{accessor} returns ({', '.join(open_[:6])}{', ...' if len(open_) > 6 else ''}): "
                    "the prompt shows one operation under two owners, and no accepted decision keeps both."
                ),
                "hint": (
                    f"not decided — decide: remove the {owner} duplicates and let callers use "
                    f"<method> of the {accessor} repository, or record in State 2 the decision that keeps "
                    f"each duplicate, naming it as {owner}.<method> (NOTE_GATE.md 'One operation, one owner')."
                ),
            })
    return findings
