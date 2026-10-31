"""Pinned text versions and the verbatim passages the experiment rests on.

Every normative element of the model, every witness basis and every claim of
the packet names a passage here by key. `check_quotes.py` reads each passage
from git at the named commit and fails if it is not found verbatim (white
space normalised, as the questions judge does). A key is evidence that the
passage existed at that commit, not that the model translates it correctly:
the translation is argued in `TRACEABILITY.md`.
"""
from __future__ import annotations

CASE = "examples/registry"
PRODUCT = f"{CASE}/00_product.md"
MODELS = f"{CASE}/01_models.md"
AUDIT = f"{CASE}/02_rules_audit.md"
RECORDS = f"{CASE}/02_rules_records.md"
ACCESS = f"{CASE}/02_rules_access.md"
INSTALL = f"{CASE}/02_rules_installation.md"

# The canonical ref the experiment starts from (PROJECT_INDEX.json: registry ->
# agent/registry, examples/registry), and the generic tooling it was run with.
CANONICAL_REF = "agent/registry"
CANONICAL_SHA = "cf675e5c9d284b7578740d5b074843da066d0d4b"
TOOLS_MAIN_SHA = "22d05dbf0394d8c0974ba65c42db8168a75b9fb6"
QUESTIONS_WORKBENCH_LAST_CHANGE = "736d1aca4810f8ddae9b3a5a56433c79172ba43d"

# Text versions of the cluster. `rounds` are the State 2 question rounds whose
# recorded document digests (summary.json "documents") equal the audit text of
# that commit; provenance.py recomputes the mapping.
VERSIONS: dict[str, dict] = {
    "V0": {"sha": "fd254d08", "label": "State 2 draft", "rounds": [1],
           "numbering": "ever", "seq_scope_s1": "global",
           "empty_erasure": "nothing", "a14_exception": False, "a14_r5_exception": False,
           "a15_inv_erasure_entry": "unconditional"},
    "V1": {"sha": "cb9f12d3", "label": "answers to round 1", "rounds": [2, 3, 4],
           "numbering": "durable", "seq_scope_s1": "global",
           "empty_erasure": "nothing", "a14_exception": False, "a14_r5_exception": False,
           "a15_inv_erasure_entry": "unconditional"},
    "V2": {"sha": "12e2d9ea", "label": "answers to round 4 (invariant weakened)", "rounds": [5],
           "numbering": "durable", "seq_scope_s1": "global",
           "empty_erasure": "nothing", "a14_exception": False, "a14_r5_exception": False,
           "a15_inv_erasure_entry": "if_removed"},
    "V2r": {"sha": "37beed89", "label": "answers to round 5 (numbers issued again after a restore)",
            "rounds": [6],
            "numbering": "reissue_after_restore", "seq_scope_s1": "global",
            "empty_erasure": "nothing", "a14_exception": False, "a14_r5_exception": False,
            "a15_inv_erasure_entry": "if_removed"},
    "V3a": {"sha": "9cb4051e", "label": "answers to round 6 (instance marks)", "rounds": [7],
            "numbering": "marks", "seq_scope_s1": "global",
            "empty_erasure": "nothing", "a14_exception": False, "a14_r5_exception": False,
            "a15_inv_erasure_entry": "if_removed"},
    "V3b": {"sha": "af52b3fa", "label": "answers to round 7 (marks; a failed change skips)",
            "rounds": [8],
            "numbering": "marks_skip", "seq_scope_s1": "global",
            "empty_erasure": "nothing", "a14_exception": False, "a14_r5_exception": False,
            "a15_inv_erasure_entry": "if_removed"},
    "V4": {"sha": "67589757", "label": "answers to round 9 and R0-89", "rounds": [10, 11],
           "numbering": "history", "seq_scope_s1": "history",
           "empty_erasure": "nothing", "a14_exception": False, "a14_r5_exception": False,
           "a15_inv_erasure_entry": "if_removed"},
    "V5": {"sha": "699d18f3", "label": "answers to round 11 (empty erasure writes its entry)",
           "rounds": [12],
           "numbering": "history", "seq_scope_s1": "history",
           "empty_erasure": "entry_with_conf", "a14_exception": True, "a14_r5_exception": False,
           "a15_inv_erasure_entry": "unconditional"},
    # constructed, not historical: V4 with only A15 rule 6 (and its Required
    # test) replaced by the V5 wording — the edit a round 11 T9 reader would
    # make if they changed only the passage the judge quoted
    "H1": {"sha": "67589757", "label": "CONSTRUCTED: V4 + new A15 rule 6 only", "rounds": [], "constructed": True,
           "numbering": "history", "seq_scope_s1": "history",
           "empty_erasure": "entry_with_conf", "a14_exception": False, "a14_r5_exception": False,
           "a15_inv_erasure_entry": "if_removed"},
    "V6": {"sha": "b31d9eac", "label": "answers to round 12 (A14 rule 5 follows); current",
           "rounds": list(range(13, 35)),
           "numbering": "history", "seq_scope_s1": "history",
           "empty_erasure": "entry_with_conf", "a14_exception": True, "a14_r5_exception": True,
           "a15_inv_erasure_entry": "unconditional"},
}

# key -> (commit, path, verbatim passage)
Q: dict[str, tuple[str, str, str]] = {
    # ---- State 0 -------------------------------------------------------
    "R0-66.row": ("fd254d08", PRODUCT,
                  "| erase audit entries before a date | owner, confirming | every entry older than the "
                  "date the owner gives is gone; the erasure leaves an entry of its own naming the date (R0-66) | — |"),
    "R0-66.text": ("fd254d08", PRODUCT,
                   "In the periodic review the owner erases, confirming, every entry older than a date the "
                   "owner gives; that erasure leaves an entry of its own naming the date. Registry erases no "
                   "entry on its own."),
    "R0-37.audit": ("fd254d08", PRODUCT,
                    "the project or customer, the outcome, the contract and release version, and a "
                    "confirmation id where the owner confirmed."),
    "R0-58.scope": ("fd254d08", PRODUCT,
                    "Registry records only significant changes of state: changes to projects and customer "
                    "records, granting and revoking an agent session's projects, restricting processing and "
                    "lifting it, and erasures and anonymisations."),
    "R0-58.reads": ("fd254d08", PRODUCT,
                    "Ordinary reads, agent calls and the inner steps of flows are not recorded in Registry"),
    "R0-60.every_erasure": ("fd254d08", PRODUCT,
                            "a log entry for every erasure, without the erased values (R0-58)."),
    "R0-12.row": ("fd254d08", PRODUCT,
                  "archiving an archived project returns it unchanged (R0-12)"),
    "R0-89.title": ("67589757", PRODUCT,
                    "### R0-89 — Restoring a lost store is disaster recovery, outside Registry's guarantees "
                    "(owner, 2026-10-31, after State 2 rounds 5–9; narrows R0-58, R0-79)"),
    "R0-89.history": ("cf675e5c", PRODUCT,
                      "Registry's guarantees — the log's numbering, the closed import — hold within each "
                      "store's history"),
    # ---- State 1 -------------------------------------------------------
    "M09.seq.global": ("fd254d08", MODELS,
                       "then one more than the last ever written; never reused, also after old"),
    "M09.seq.history": ("67589757", MODELS,
                        "one more than the last its store's history ever wrote; never reused within"),
    "M09.erasure_writes": ("fd254d08", MODELS,
                           "and the erasure of old entries itself (R0-66)"),
    "M09.conf": ("fd254d08", MODELS,
                 "the confirmation id where the owner confirmed (R0-37; \"Identity formats\");"),
    "M09.subject_none": ("cf675e5c", MODELS,
                         "none for an erasure of old entries, whose fact is the owner's date;"),
    "ID.conf_minted": ("cf675e5c", MODELS,
                       "Registry mints a confirmation id when the owner confirms an action that asks for "
                       "confirmation — archiving a project, erasing an archived project, the import, erasing "
                       "old audit entries (Primary actions) — and writes it once into the audit entry of that "
                       "action (M09)"),
    "M09.open_q": ("fd254d08", MODELS,
                   "Whether refused attempts and agent-authority reads leave an entry is State 2's"),
    # ---- State 2: A14 --------------------------------------------------
    "A14.r1": ("fd254d08", AUDIT,
               "An entry is written by an accepted action that changes state and that M09 lists, in the same "
               "transaction as the change: if the change is not stored, neither is the entry, and the reverse."),
    "A14.r2": ("fd254d08", AUDIT,
               "A refused action writes no entry — a stale revision, a failed check of rights, an unknown id, "
               "a refused sign-in included."),
    "A14.r3.old": ("fd254d08", AUDIT,
                   "3. An accepted action that changes nothing (A03 rule 4, A05) writes no entry.\n4."),
    "A14.r3.new": ("699d18f3", AUDIT,
                   "An accepted action that changes nothing (A03 rule 4, A05) writes no entry, but for the "
                   "erasure of old audit entries (A15 rule 6)."),
    "A14.r4": ("fd254d08", AUDIT,
               "Reads write no entry, whoever reads — the owner, a service, Kernel for the agent (R0-58)."),
    "A14.r5.old": ("fd254d08", AUDIT,
                   "A confirmation id is minted only for an accepted, confirmed action that changes state, and "
                   "is written into its entry (and, for the import, into the migration closure); a confirmed "
                   "action that changes nothing mints none."),
    "A14.r5.new": ("b31d9eac", AUDIT,
                   "a confirmed action that changes nothing mints none, but for the erasure of old audit "
                   "entries, which always writes its entry with its confirmation id (A15 rule 6)."),
    "A14.inv.old": ("fd254d08", AUDIT,
                    "entry e exists <=> accepted action a with changed(a) and a in M09.actions and e written "
                    "in the transaction of a"),
    "A14.inv.new": ("699d18f3", AUDIT,
                    "entry e exists <=> accepted action a in M09.actions, with changed(a) or a an erasure of "
                    "old entries, and e written in the transaction of a"),
    "A14.t2": ("fd254d08", AUDIT,
               "Archiving an archived project leaves the log unchanged and mints no confirmation id."),
    "A14.t3": ("fd254d08", AUDIT,
               "A failure while storing a correction leaves neither the change nor its entry."),
    # ---- State 2: A15 --------------------------------------------------
    "A15.r1": ("fd254d08", AUDIT,
               "No action changes an entry. Entries are added by A14 and removed only by 'erase audit entries "
               "before a date' (R0-66); Registry has no other path that removes one."),
    "A15.r3": ("cb9f12d3", AUDIT,
               "The date of an erasure is a date not later than today, the current date in UTC; a later date "
               "is refused. Every entry whose instant is before 00:00 UTC of that date is removed."),
    "A15.r4": ("fd254d08", AUDIT,
               "The erasure's own entry is written after the removal, in the same transaction, with the "
               "current instant; it is therefore never removed by the erasure that wrote it."),
    "A15.r5.ever": ("fd254d08", AUDIT,
                    "Sequence numbers are never reused (M09): the next entry after an erasure continues from "
                    "the last number ever written."),
    "A15.r5.durable": ("cb9f12d3", AUDIT,
                       "Registry keeps that last number durably, apart from the entries, so neither an erasure "
                       "nor a restart lowers it."),
    "A15.r5.reissue": ("37beed89", AUDIT,
                       "the entries written after it are lost and exist nowhere, and their numbers are issued "
                       "again for new entries."),
    "A15.r5.marks": ("9cb4051e", AUDIT,
                     "Registry records each number in the instance marks — a small file in the backup location, "
                     "apart from the store and the backups, which a restore does not replace (A18) — before "
                     "the entry commits; at start it continues from the higher of the store's last number and "
                     "the marks'."),
    "A15.r5.marks_skip": ("af52b3fa", AUDIT,
                          "a change that then fails leaves its number unused for ever, and the log skips it."),
    "A15.r5.history": ("67589757", AUDIT,
                       "Sequence numbers are never reused within a store's history (M09): changes that write an "
                       "entry are applied one at a time, and each entry takes the number after the last that "
                       "history ever wrote, kept in the store apart from the entries, so an erasure does not "
                       "lower it."),
    "A15.r6.old": ("fd254d08", AUDIT,
                   "An erasure that removes no entry changes nothing: it is accepted, writes no entry and mints "
                   "no confirmation id (A14)."),
    "A15.r6.new": ("699d18f3", AUDIT,
                   "An erasure that removes no entry still writes its own entry naming the date, with its "
                   "confirmation id: R0-66 makes the erasure leave an entry of its own, whatever it removed. "
                   "It is the one accepted action that writes an entry without changing other state (A14 rule 3)."),
    "A15.inv.seq": ("fd254d08", AUDIT,
                    "for entries e1 written before e2: e1.sequence < e2.sequence"),
    "A15.inv.removed": ("fd254d08", AUDIT,
                        "erase(d) accepted => no entry with instant < start_of(d) remains"),
    "A15.inv.entry.v0": ("fd254d08", AUDIT,
                         "and the erasure entry e has e.instant >= start_of(d)"),
    "A15.inv.entry.v2": ("12e2d9ea", AUDIT,
                         "erase(d) accepted and removed at least one entry => its erasure entry e has e.instant "
                         ">= start_of(d)"),
    "A15.inv.entry.v5": ("699d18f3", AUDIT,
                         "erase(d) accepted => its erasure entry e has e.instant >= start_of(d)"),
    "A15.t1": ("fd254d08", AUDIT,
               "In a log whose entries are all older than today, erasing before today leaves exactly the new "
               "erasure entry."),
    "A15.t2.old": ("fd254d08", AUDIT,
                   "Erasing before a date older than every entry removes nothing, writes no entry and mints no "
                   "confirmation id."),
    "A15.t2.new": ("699d18f3", AUDIT,
                   "Erasing before a date older than every entry removes nothing and writes its own erasure "
                   "entry with a confirmation id."),
    "A15.t3": ("fd254d08", AUDIT, "A date later than today is refused."),
    "A15.t4": ("fd254d08", AUDIT,
               "After an erasure, the next entry's sequence number is one more than the erasure entry's."),
    # ---- State 2: A03 / A04 / A05 / A01 / A13 ---------------------------
    "A03.r4": ("fd254d08", RECORDS,
               "A correction that gives exactly the stored facts is accepted and changes nothing: revision "
               "and last-changed instant stay, and no audit entry is written (A05)."),
    "A04.r2": ("fd254d08", RECORDS,
               "A stated revision that is not the record's current one is refused as stale, and nothing "
               "changes (R0-35)."),
    "A04.r3": ("cf675e5c", RECORDS,
               "An action that would change nothing (A03 rule 4, A05) still states the revision and is "
               "refused when it is stale."),
    "A04.r4": ("fd254d08", RECORDS, "Every action is atomic: it applies all its changes or none."),
    "A04.r6.order": ("cf675e5c", RECORDS,
                     "(3) that every record the action names exists — its target and any it newly names, such "
                     "as a customer; (4) the values given (A02, A08, A22); (5) the stated revision or access "
                     "version (A12); (6) the record's lifecycle — archived, erased, anonymised, not in the "
                     "set, a customer's eligibility, a conflict."),
    "A04.r6.first": ("cf675e5c", RECORDS,
                     "checks in one order, and the first failure is its answer"),
    "A04.r6.stage1": ("cf675e5c", RECORDS,
                      "then for a change its CSRF value (R0-29), then a confirmation value where one is asked "
                      "(A13);"),
    "A04.r6.every_one": ("430f4d4c", RECORDS,
                         "When several checks of one stage fail, the answer names every one of them."),
    "A04.t4": ("cf675e5c", RECORDS,
               "Correcting an archived project with a stale revision is refused as stale, not as archived."),
    "A04.t3": ("fd254d08", RECORDS,
               "Archiving moves the revision once; archiving again with the new revision answers the project "
               "unchanged."),
    "A05.r1.head": ("cf675e5c", RECORDS,
                    "A transition to the state a record is already in, that passes every check of A04 rule 6, "
                    "is accepted and changes nothing: archiving an archived project (R0-12)"),
    "A05.r1.tail": ("cf675e5c", RECORDS,
                    "clearing an active project that is already clear, registering a registered session (R0-53)."),
    "A05.r2": ("fd254d08", RECORDS,
               "Such a transition answers the record as it stands; its revision, its last-changed instant and "
               "a session's access version stay; no audit entry is written and no confirmation id is minted."),
    "A01.r4": ("cf675e5c", RECORDS,
               "is a repeat when the facts it supplies equal that record's current facts of the same kind: "
               "Registry answers the record as it stands now and changes nothing."),
    "A01.r5": ("cf675e5c", RECORDS,
               "A create whose request id an existing record carries, with facts that differ from that "
               "record's current ones — a different value, or the record corrected since — is refused, and "
               "nothing changes; the caller reads the record."),
    "A01.t1": ("cf675e5c", RECORDS,
               "Two 'create a project' calls with the same request id and equal facts make one project; the "
               "second answers it."),
    "A06.r6": ("cf675e5c", RECORDS, "'Read the audit log': by sequence number, ascending (M09)."),
    "A18.last_seq": ("cf675e5c", INSTALL, "0 for a store that never wrote one"),
    "A16.import_conf": ("fd254d08", AUDIT, "(and, for the import, into the migration closure)"),
    "SO1.r1T7": ("cf675e5c", f"{CASE}/questions/state1/round-01/summary.json",
                 "Whether confirmed no-op or refused actions mint confirmation ids and create AuditEntries"),
    "A13.r6.used": ("cf675e5c", ACCESS,
                    "is used up by the first submission that carries it, whatever its answer; a refused "
                    "submission needs the step shown again."),
    "A13.r6.not_id": ("cf675e5c", ACCESS,
                      "It is not the confirmation id, which Registry mints only when the action is accepted "
                      "(A14)."),
    "A18.restore.v0": ("fd254d08", INSTALL,
                       "After restoring production from a backup, the owner repeats every erasure"),
}


def quote(key: str) -> str:
    return Q[key][2]
