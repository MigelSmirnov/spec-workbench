"""Verbatim passages this experiment rests on, pinned to a commit and file.

`check_quotes.py` verifies each one with git; packet, investigation, witnesses
and the patch cite them as [q:<key>]. Unless noted, the commit is the current
canonical text cf675e5c (origin/agent/registry).
"""
from __future__ import annotations

CASE = "examples/registry"
PRODUCT = f"{CASE}/00_product.md"
MODELS = f"{CASE}/01_models.md"
RECORDS = f"{CASE}/02_rules_records.md"
ACCESS = f"{CASE}/02_rules_access.md"
AUDIT = f"{CASE}/02_rules_audit.md"
CUR = "cf675e5c"

Q: dict[str, tuple[str, str, str]] = {
    # ---- State 0 -------------------------------------------------------
    "S0.erase_row": (CUR, PRODUCT,
        "| erase a customer's contact data | owner | the Customer keeps only its identity and the fact that it "
        "was erased; name, phone, e-mail and language are gone; projects still name it (R0-06) | unknown "
        "customer refused; erasing an erased customer returns it unchanged |"),
    "S0.erase_row.origin": ("7fb4e3af", PRODUCT,
        "unknown customer refused; erasing an erased customer returns it unchanged |"),
    "S0.erase_row.origin_why": ("7fb4e3af", "-", "a repeated erasure is a no-op"),   # commit message, checked separately
    "S0.correct_row": (CUR, PRODUCT,
        "unknown customer refused; an erased customer cannot be corrected; a stale revision refused (R0-35)"),
    "S0.restrict_row": (CUR, PRODUCT, "| unknown or erased customer refused |"),
    "S0.end_row": (CUR, PRODUCT,
        "| unknown or erased customer refused; an end date later than today refused (R0-84) |"),
    "S0.archive_row": (CUR, PRODUCT,
        "archiving an archived project returns it unchanged (R0-12) | unknown id refused |"),
    "S0.erase_project_row": (CUR, PRODUCT,
        "unknown or active project refused; anonymising an anonymised project returns it unchanged, and "
        "deleting it whole is refused (R0-71)"),
    "R0-35": (CUR, PRODUCT,
        "A project, a customer and an object carry a revision that every accepted change moves. A change "
        "states the revision it was made against; a change against an older revision is refused and nothing "
        "changes. Every change is atomic."),
    "R0-35.date": (CUR, PRODUCT,
        "### R0-35 — Records carry a revision; stale changes are refused (owner, 2026-10-27; vNext §3.1, §11)"),
    "R0-06.nothing_else": (CUR, PRODUCT,
        "Erasing leaves the Customer's identity and the fact that it was erased, nothing else — the name does "
        "not survive."),
    "R0-67": (CUR, PRODUCT,
        "the Customer keeps its identity and the fact that it was erased, and projects keep naming it. There "
        "is no action that deletes a Customer whole."),
    "R0-71": (CUR, PRODUCT,
        "An anonymised project stays as it is: anonymising it again returns it unchanged, and deleting it "
        "whole is refused."),
    "R0-62": (CUR, PRODUCT,
        "'Read a project', `context`, 'list rooms' and the agent projection answer that it was erased, and "
        "'list projects' never lists it."),
    # ---- State 1 -------------------------------------------------------
    "M04.erased": (CUR, MODELS,
        "and so are its kind, its revision, its recorded instant, the request id of its create and its "
        "restricted and ended marks;"),
    "M04.erased_refused": (CUR, MODELS,
        "restricting, lifting, ending and resuming an erased Customer are refused (Primary actions)."),
    "M04.read_erased": (CUR, MODELS,
        "An erased Customer is read as its `customer_ref`, the erased mark and its instant, and no other value;"),
    "RT.state2": (CUR, MODELS,
        "Which actions must state the revision they were made against is State 2's (carried, R0-35)."),
    "RT.stale": (CUR, MODELS,
        "A change names the revision it was made against; a stale one is refused and nothing changes."),
    "M01.anon_revision": (CUR, MODELS, "name, alias, object, customer link, rooms, revision, the request id"),
    "ID.confirmed": (CUR, MODELS,
        "confirmation id when the owner confirms an action that asks for confirmation — archiving a project, "
        "erasing an archived project, the import, erasing old audit entries (Primary actions)"),
    # ---- State 2 -------------------------------------------------------
    "A04.r1": (CUR, RECORDS,
        "Erasing a project or a Customer's contact data states the revision it was made against and leaves "
        "no revision behind (M01, M04): the record is anonymised, erased or deleted, not given a next revision."),
    "A04.r1.list": (CUR, RECORDS,
        "correcting, archiving and erasing a project; correcting a customer, erasing its contact data, "
        "restricting and lifting, ending and resuming the relationship."),
    "A04.r2": (CUR, RECORDS,
        "A stated revision that is not the record's current one is refused as stale, and nothing changes "
        "(R0-35)."),
    "A04.r3": (CUR, RECORDS,
        "An action that would change nothing (A03 rule 4, A05) still states the revision and is refused when "
        "it is stale. An anonymised project and an erased Customer have no revision (M01, M04): an action on "
        "them states none."),
    "A04.r6.kind": (CUR, RECORDS,
        "and each check an operation states belongs to the stage of its kind"),
    "A04.r6.stages": (CUR, RECORDS,
        "(4) the values given (A02, A08, A22); (5) the stated revision or access version (A12); (6) the "
        "record's lifecycle — archived, erased, anonymised, not in the set, a customer's eligibility, a "
        "conflict."),
    "A04.r6.repeat": (CUR, RECORDS,
        "A transition that passes all six may be a repeat that changes nothing (A05)."),
    "A04.inv": (CUR, RECORDS,
        "for action a on record r in {Project, Customer} that may move r.revision: a.stated_revision != "
        "r.revision => refused, r unchanged"),
    "A04.inv.none": (CUR, RECORDS, "accepted erasure, anonymisation or deletion => r has no revision after"),
    "A04.t3": (CUR, RECORDS,
        "Archiving moves the revision once; archiving again with the new revision answers the project "
        "unchanged."),
    "A04.t4": (CUR, RECORDS,
        "Correcting an archived project with a stale revision is refused as stale, not as archived."),
    "A04.consequence": (CUR, RECORDS,
        "the owner interface always shows and sends the revision of the card it rendered."),
    "A05.r1": (CUR, RECORDS,
        "A transition to the state a record is already in, that passes every check of A04 rule 6, is "
        "accepted and changes nothing:"),
    "A05.r1.erased": (CUR, RECORDS,
        "anonymising an anonymised one (R0-71), erasing an erased Customer (Primary actions)"),
    "A05.r2": (CUR, RECORDS,
        "Such a transition answers the record as it stands; its revision, its last-changed instant and a "
        "session's access version stay; no audit entry is written and no confirmation id is minted."),
    "A05.r4": (CUR, RECORDS,
        "The refusals State 0 states stay refusals and come first:"),
    "A05.r4.anon": (CUR, RECORDS, "deleting an anonymised project whole (R0-71)"),
    "A05.consequence": (CUR, RECORDS,
        "The audit log holds changes only (R0-58), and a retried transition is safe."),
    "A01.consequence": (CUR, RECORDS,
        "Kernel's retried 'add a room' or publish and a resubmitted owner form are safe"),
    "A02.r1": (CUR, RECORDS,
        "A required value given as an empty string or as white space only is missing, and the action is "
        "refused as for a missing value"),
    "A13.r6.bind": (CUR, ACCESS,
        "bound to the action, its target, the revision or access version the step showed, and its inputs"),
    "A13.r6.used": (CUR, ACCESS,
        "is used up by the first submission that carries it, whatever its answer; a refused submission needs "
        "the step shown again."),
    "A13.r2.sessions": (CUR, ACCESS, "Several owner sessions may be open at once; signing in ends none of the others."),
    "A14.r2": (CUR, AUDIT,
        "A refused action writes no entry — a stale revision, a failed check of rights, an unknown id, a "
        "refused sign-in included."),
    "A14.r3": (CUR, AUDIT,
        "An accepted action that changes nothing (A03 rule 4, A05) writes no entry, but for the erasure of "
        "old audit entries (A15 rule 6)."),
    # ---- rounds --------------------------------------------------------
    "S0r18.single": (CUR, f"{CASE}/questions/state0/round-18/summary.json",
        "For an exact retry of a successful archive or customer erasure carrying the old revision, does "
        "idempotent success or stale-revision refusal take precedence?"),
    "S0r26.T3": (CUR, f"{CASE}/questions/state0/round-26/summary.json",
        "including nominally idempotent actions such as archiving an archived project or erasing an erased customer?"),
    "S2r08.single": (CUR, f"{CASE}/questions/state2/round-08/summary.json",
        "What happens when the owner submits archive for an anonymised project, and must that submission "
        "state a revision?"),
}
