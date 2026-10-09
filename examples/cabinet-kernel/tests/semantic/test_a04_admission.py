"""Witness tests for accepted decision A04 (02_rules_functions.md).

Admission runs an implementation over its contract version's whole corpus, in
the order cases were first added, and a submission activates what it admits.
Each test carries the witness name its Required test declares.

The Factory project supplies the ``semantic_runtime`` pytest fixture. It binds
these scenarios to the generated public operations of State 5 — named here by
their operation names, with arguments shaped as the State 6 models — without
changing the assertions below. Each test gets a fresh, empty kernel store.

Fixture surface used here:

- ``issue_contract_version(slot_id, purpose, inputs, outputs)`` ->
  contract_version_id; the fixture supplies resource bounds within the
  installation's ceilings (A04 does not depend on them) and acts as agent
  ``author``;
- ``add_trial_case(contract_version_id, inputs, expected_outputs=None)`` ->
  ShownAddedTrialCase; values are RequestJsonValue dicts;
- ``submit_implementation(contract_version_id, code)`` -> ShownSubmission
  (implementation, AdmissionVerdict M08, Activation M09 or none);
- ``roll_back_slot(slot_id, implementation_id, actor=...)`` -> Activation;
  the owner unless ``actor=`` names an author;
- ``compose_flow_version``, ``activate_flow_version``, ``start_run`` and
  ``capture_failed_execution(execution, contract_version_id)`` -> ShownTrialCase
  for a captured case;
- ``read_slot(slot_id)`` -> SlotHistory, ``get_repair_view(slot_id)`` ->
  RepairView, ``page_records(record_type, record_filter, page_size)`` ->
  RecordPageAnswer, to read back what was recorded.

One capability: ``mcp_request`` with ``installation.owner_token`` and
``installation.agent_token(name)``, to send requests no call of the table can
shape (an unknown operation, an unknown field).
"""

import hashlib
import json

import pytest

TEXT = '{"type":"string"}'

OWNER = {"kind": "owner", "agent_name": None}
AUTHOR = {"kind": "agent", "agent_name": "author"}

ECHO = """
def run(inputs):
    return {"y": inputs["x"]}
"""

# Echoes, but crashes on the input "boom".
FRAGILE = """
def run(inputs):
    if inputs["x"] == "boom":
        raise ValueError("boom")
    return {"y": inputs["x"]}
"""


def _port(name, direction, schema, disclosure_class=None):
    return {
        "name": name,
        "direction": direction,
        "value_schema": schema,
        "carriage": "value",
        "media_type": None,
        "cardinality": "one",
        "disclosure_class": disclosure_class,
    }


def _json(port, value):
    return {"payload_kind": "json", "port": port, "json_text": json.dumps(value)}


def _function(semantic_runtime, slot_id):
    """A function of one text input `x` and one text output `y`."""
    return semantic_runtime.issue_contract_version(
        slot_id,
        purpose=f"A04 witness: {slot_id}",
        inputs=[_port("x", "input", TEXT, "open")],
        outputs=[_port("y", "output", TEXT)],
    )


def _case(semantic_runtime, contract_version_id, x, y=None):
    expected = None if y is None else [_json("y", y)]
    added = semantic_runtime.add_trial_case(
        contract_version_id, inputs=[_json("x", x)], expected_outputs=expected
    )
    return added.trial_case.trial_case_id


def _value(enum_or_value):
    return getattr(enum_or_value, "value", enum_or_value)


def _history(semantic_runtime, slot_id, contract_version_id):
    slot = semantic_runtime.read_slot(slot_id)
    (history,) = [
        h
        for h in slot.contract_versions
        if h.contract_version.contract_version_id == contract_version_id
    ]
    return history


def _implementation_history(history, implementation_id):
    (found,) = [i for i in history.implementations if i.implementation_id == implementation_id]
    return found


def _trial_executions(semantic_runtime, implementation_id):
    return semantic_runtime.page_records(
        "trial_execution",
        {"filter_kind": "equals", "field": "implementation_id", "value": implementation_id},
        page_size=200,
    ).records.trial_executions


def _corpus_digest(trial_case_ids):
    """The corpus digest of A04 rule 2: the content identity (State 6 decision
    14, A01 rule 1) of the CorpusContent holding the ids in corpus order — the
    lowercase hex SHA-256 of its RFC 8785 canonical JSON. Every key and id is
    ASCII, so sorted keys and no whitespace give exactly the JCS bytes; the id
    list keeps its order (corpus order carries meaning)."""
    facts = {"subject_kind": "corpus", "trial_case_ids": list(trial_case_ids)}
    text = json.dumps(facts, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _submit(semantic_runtime, contract_version_id, code):
    submission = semantic_runtime.submit_implementation(contract_version_id, code)
    return submission, submission.implementation.implementation_id


def test_empty_corpus_refused(semantic_runtime):
    """[witness: verification:kernel_a04_empty_corpus_refused]

    A04 Required test 1: An implementation for a contract version with no cases
    is refused as `empty_corpus` and nothing is activated.
    """
    cv = _function(semantic_runtime, "a04_empty")

    submission, implementation_id = _submit(semantic_runtime, cv, ECHO)
    # A04 rule 3: refused with reason empty_corpus when the corpus is empty;
    # rule 4: a refused verdict activates nothing.
    assert _value(submission.verdict.verdict) == "refused"
    assert submission.verdict.reason.reason_kind == "empty_corpus"
    assert len(submission.verdict.trial_executions) == 0
    assert submission.activation is None

    history = _history(semantic_runtime, "a04_empty", cv)
    assert history.serving_activation is None
    assert _implementation_history(history, implementation_id).admitted_over_current_corpus is False
    assert len(_trial_executions(semantic_runtime, implementation_id)) == 0

    # Control: once the corpus holds a case the same code is admitted and
    # activated, so the refusal above is the empty corpus, not the code.
    _case(semantic_runtime, cv, "hello", "hello")
    submission, again_id = _submit(semantic_runtime, cv, ECHO)
    assert again_id == implementation_id
    assert _value(submission.verdict.verdict) == "admitted"
    assert submission.activation.implementation_id == implementation_id


def test_refusal_names_first_failing_case(semantic_runtime):
    """[witness: verification:kernel_a04_refusal_names_first_failing_case]

    A04 Required test 2: With cases c1, c2, c3 added in that order and c2, c3
    failing, the reason names c2; the verdict still records three executions.
    """
    cv = _function(semantic_runtime, "a04_first_failing")
    c1 = _case(semantic_runtime, cv, "hello", "hello")
    # c2 fails by its expected output, c3 by a crash: two different outcomes,
    # so the reason shows which failing case it names.
    c2 = _case(semantic_runtime, cv, "world", "not the echo")
    c3 = _case(semantic_runtime, cv, "boom")

    submission, implementation_id = _submit(semantic_runtime, cv, FRAGILE)
    verdict = submission.verdict
    # A04 rule 3: the first case in corpus order that did not pass, and its
    # outcome; outputs that validate but differ are output_mismatch.
    assert _value(verdict.verdict) == "refused"
    assert verdict.reason.reason_kind == "failing_case"
    assert verdict.reason.trial_case_id == c2
    assert _value(verdict.reason.outcome) == "output_mismatch"
    assert submission.activation is None

    # A04 rule 2: every case, in corpus order, never stopping early.
    assert len(verdict.trial_executions) == 3
    by_id = {e.trial_execution_id: e for e in _trial_executions(semantic_runtime, implementation_id)}
    executed = [by_id[t] for t in verdict.trial_executions]
    assert [e.trial_case_id for e in executed] == [c1, c2, c3]
    assert [_value(e.outcome) for e in executed] == ["passed", "output_mismatch", "crashed"]


def test_admitted_submission_activates_once(semantic_runtime):
    """[witness: verification:kernel_a04_admitted_submission_activates_once]

    A04 Required test 3: Submitting an admitted implementation activates it,
    the Activation recorded by the kernel; submitting it again changes nothing.
    """
    cv = _function(semantic_runtime, "a04_activates_once")
    _case(semantic_runtime, cv, "hello", "hello")

    first, implementation_id = _submit(semantic_runtime, cv, ECHO)
    assert _value(first.verdict.verdict) == "admitted"
    activation = first.activation
    # A04 rule 4: followed at once, in the same request, by an Activation by
    # the kernel.
    assert activation.implementation_id == implementation_id
    assert activation.contract_version_id == cv
    assert _value(activation.activated_by.kind) == "kernel"
    assert activation.activated_by.agent_name is None
    executions_after_first = len(_trial_executions(semantic_runtime, implementation_id))
    assert executions_after_first == 1

    second, again_id = _submit(semantic_runtime, cv, ECHO)
    # A01 rule 4 / A04 rule 2: the same implementation and the reused verdict;
    # rule 4: already current, so nothing is recorded and the current
    # activation is returned.
    assert again_id == implementation_id
    assert second.implementation.submitted_at == first.implementation.submitted_at
    assert second.verdict == first.verdict
    assert second.activation.store_position == activation.store_position
    assert len(_trial_executions(semantic_runtime, implementation_id)) == executions_after_first

    history = _history(semantic_runtime, "a04_activates_once", cv)
    assert history.serving_activation.store_position == activation.store_position
    assert len(_implementation_history(history, implementation_id).verdicts) == 1

    # Control: when another implementation is current, the same resubmission
    # does activate again — a new record, by the kernel, on the reused verdict —
    # so "nothing" above comes from being current, not from resubmission
    # never activating.
    other, other_id = _submit(semantic_runtime, cv, ECHO + "\n# second\n")
    assert other.activation.implementation_id == other_id
    third, _ = _submit(semantic_runtime, cv, ECHO)
    assert third.verdict == first.verdict
    assert third.activation.implementation_id == implementation_id
    assert third.activation.store_position > other.activation.store_position
    assert _value(third.activation.activated_by.kind) == "kernel"
    assert len(_trial_executions(semantic_runtime, implementation_id)) == executions_after_first


def test_resubmission_readmits_grown_corpus(semantic_runtime):
    """[witness: verification:kernel_a04_resubmission_readmits_grown_corpus]

    A04 Required test 4: After a failed run is captured, submitting the earlier
    implementation again runs admission over the grown corpus; it is activated
    only when it passes.
    """
    cv = _function(semantic_runtime, "a04_grown_corpus")
    c1 = _case(semantic_runtime, cv, "hello")

    robust, robust_id = _submit(semantic_runtime, cv, ECHO)
    assert _value(robust.verdict.verdict) == "admitted"
    fragile, fragile_id = _submit(semantic_runtime, cv, FRAGILE)
    assert _value(fragile.verdict.verdict) == "admitted"
    serving = fragile.activation
    assert serving.implementation_id == fragile_id
    old_digest = fragile.verdict.corpus_digest

    # A run of the fragile implementation fails on "boom".
    composed = semantic_runtime.compose_flow_version(
        "a04_grown_corpus_flow",
        purpose="A04 witness: grown corpus",
        inputs=[_port("x", "input", TEXT, "open")],
        outputs=[_port("y", "output", TEXT)],
        nodes=[
            {
                "node_id": "f",
                "kind": "function",
                "contract_version_id": cv,
                "binding_id": None,
                "map_over": None,
            }
        ],
        edges=[
            {"from_node": "", "from_port": "x", "to_node": "f", "to_port": "x", "guard": None},
            {"from_node": "f", "from_port": "y", "to_node": "", "to_port": "y", "guard": None},
        ],
        constants=[],
    )
    semantic_runtime.activate_flow_version(composed.flow_version.flow_version_id)
    run = semantic_runtime.start_run("a04_grown_corpus_flow", [_json("x", "boom")])
    assert _value(run.status) == "failed"
    (failed,) = semantic_runtime.page_records(
        "node_execution",
        {"filter_kind": "equals", "field": "run_id", "value": run.run_id},
        page_size=200,
    ).records.node_executions
    assert _value(failed.status) == "crashed"

    captured = semantic_runtime.capture_failed_execution(
        {
            "run_id": failed.run_id,
            "node_id": failed.node_id,
            "map_index": failed.map_index,
            "attempt_number": failed.attempt_number,
        },
        cv,
    )
    c2 = captured.trial_case_id
    assert c2 != c1

    # A04 rule 7: the corpus digest changed; the serving implementation keeps
    # serving and visibly lacks a verdict over the current corpus.
    history = _history(semantic_runtime, "a04_grown_corpus", cv)
    new_digest = history.corpus_digest
    assert new_digest != old_digest
    assert history.serving_activation.store_position == serving.store_position
    assert _implementation_history(history, fragile_id).admitted_over_current_corpus is False

    # Resubmitting the serving implementation: admission over [c1, c2]; it
    # fails c2, so nothing is activated and its activation keeps serving.
    again, again_id = _submit(semantic_runtime, cv, FRAGILE)
    assert again_id == fragile_id
    # A04 rule 2: no verdict over the new digest existed, so admission ran.
    assert again.verdict.corpus_digest == new_digest
    assert len(again.verdict.trial_executions) == 2
    assert _value(again.verdict.verdict) == "refused"
    assert again.verdict.reason.trial_case_id == c2
    assert _value(again.verdict.reason.outcome) == "crashed"
    # A04 rule 4: a refused verdict activates nothing.
    assert again.activation is None
    history = _history(semantic_runtime, "a04_grown_corpus", cv)
    assert history.serving_activation.store_position == serving.store_position

    # Resubmitting the earlier robust implementation: admission over the grown
    # corpus passes, so it is activated by the kernel as a new record.
    earlier, earlier_id = _submit(semantic_runtime, cv, ECHO)
    assert earlier_id == robust_id
    assert earlier.verdict.corpus_digest == new_digest
    assert len(earlier.verdict.trial_executions) == 2
    assert _value(earlier.verdict.verdict) == "admitted"
    assert earlier.activation.implementation_id == robust_id
    assert earlier.activation.store_position > serving.store_position
    assert _value(earlier.activation.activated_by.kind) == "kernel"

    history = _history(semantic_runtime, "a04_grown_corpus", cv)
    assert history.serving_activation.implementation_id == robust_id
    assert _implementation_history(history, robust_id).admitted_over_current_corpus is True


def test_rollback_requires_current_verdict(semantic_runtime):
    """[witness: verification:kernel_a04_rollback_requires_current_verdict]

    A04 Required test 5: A rollback to an implementation with no verdict over
    the current corpus is refused.
    """
    slot_id = "a04_rollback"
    cv = _function(semantic_runtime, slot_id)
    _case(semantic_runtime, cv, "hello", "hello")

    _, first_id = _submit(semantic_runtime, cv, ECHO)
    second, second_id = _submit(semantic_runtime, cv, ECHO + "\n# second\n")
    assert second.activation.implementation_id == second_id

    # The corpus grows; the second implementation is re-admitted over it (it
    # is current, so no new activation), the first is not.
    _case(semantic_runtime, cv, "world", "world")
    readmitted, _ = _submit(semantic_runtime, cv, ECHO + "\n# second\n")
    assert _value(readmitted.verdict.verdict) == "admitted"
    assert readmitted.activation.store_position == second.activation.store_position
    history = _history(semantic_runtime, slot_id, cv)
    assert _implementation_history(history, first_id).admitted_over_current_corpus is False

    # A04 rule 5: an implementation without an admitted verdict over the
    # current corpus is refused; rollback runs no admission.
    executions_before = len(_trial_executions(semantic_runtime, first_id))
    with pytest.raises(Exception) as exc:
        semantic_runtime.roll_back_slot(slot_id, first_id)
    assert exc.value.code == "refused"

    # Nothing was recorded: the same activation serves, no execution, no verdict.
    after = _history(semantic_runtime, slot_id, cv)
    assert after.serving_activation.store_position == second.activation.store_position
    assert len(_trial_executions(semantic_runtime, first_id)) == executions_before
    assert _implementation_history(after, first_id).verdicts == (
        _implementation_history(history, first_id).verdicts
    )

    # Control: a third implementation admitted over the current corpus becomes
    # current, and rolling back to the second — admitted over the current
    # corpus — succeeds; the refusal above is the missing verdict.
    third, _ = _submit(semantic_runtime, cv, ECHO + "\n# third\n")
    assert third.activation is not None
    rolled = semantic_runtime.roll_back_slot(slot_id, second_id)
    assert rolled.implementation_id == second_id
    assert rolled.store_position > third.activation.store_position


def test_verdict_set_only_by_kernel(semantic_runtime):
    """[witness: verification:kernel_a04_verdict_set_only_by_kernel]

    A04 Required test 6: No operation lets the owner or an agent set a verdict.
    """
    slot_id = "a04_verdict_by_kernel"
    cv = _function(semantic_runtime, slot_id)
    _case(semantic_runtime, cv, "boom")

    refused, implementation_id = _submit(semantic_runtime, cv, FRAGILE)
    assert _value(refused.verdict.verdict) == "refused"
    before = _history(semantic_runtime, slot_id, cv)

    owner_token = semantic_runtime.installation.owner_token
    author_token = semantic_runtime.installation.agent_token("author")
    attempt = {
        "implementation_id": implementation_id,
        "corpus_digest": refused.verdict.corpus_digest,
        "verdict": "admitted",
    }
    # A04 rule 8: no actor records, edits or waives a verdict — the MCP
    # catalogue (State 5) has no such operation, for the owner or an agent.
    for operation in ("record_admission_verdict", "set_verdict", "admit_implementation"):
        for token in (owner_token, author_token):
            with pytest.raises(Exception) as exc:
                semantic_runtime.mcp_request(operation, attempt, token=token)
            assert exc.value.code == "invalid_request"

    # A verdict cannot ride along a submission: an unknown field is refused.
    with pytest.raises(Exception) as exc:
        semantic_runtime.mcp_request(
            "submit_implementation",
            {"contract_version_id": cv, "code": FRAGILE, "verdict": "admitted"},
            token=author_token,
        )
    assert exc.value.code == "invalid_request"

    # The one activating operation the owner and an author may call does not
    # waive it either, for either of them (A04 rule 5).
    for actor in (OWNER, AUTHOR):
        with pytest.raises(Exception) as exc:
            semantic_runtime.roll_back_slot(slot_id, implementation_id, actor=actor)
        assert exc.value.code == "refused"

    # Nothing changed: the one verdict is still the kernel's refusal.
    after = _history(semantic_runtime, slot_id, cv)
    implementation = _implementation_history(after, implementation_id)
    assert implementation.verdicts == _implementation_history(before, implementation_id).verdicts
    (verdict,) = implementation.verdicts
    assert _value(verdict.verdict) == "refused"
    assert implementation.admitted_over_current_corpus is False
    assert after.serving_activation is None

    # Control: the same submission request without the extra field is
    # accepted, so the refusal above is the field, not the request.
    answer = semantic_runtime.mcp_request(
        "submit_implementation",
        {"contract_version_id": cv, "code": FRAGILE},
        token=author_token,
    )
    assert _value(answer.verdict.verdict) == "refused"


def test_corpus_order_is_first_added(semantic_runtime):
    """[witness: verification:kernel_a04_corpus_order_is_first_added]

    A04 Required test 7: Adding a case equal to c1 after c3 returns c1, keeps it
    first in the corpus, and leaves the corpus digest unchanged.
    """
    slot_id = "a04_corpus_order"
    cv = _function(semantic_runtime, slot_id)
    first = semantic_runtime.add_trial_case(cv, inputs=[_json("x", "a")])
    c1 = first.trial_case.trial_case_id
    c2 = _case(semantic_runtime, cv, "b")
    c3 = _case(semantic_runtime, cv, "c")
    assert first.corpus_position == 0
    digest = _history(semantic_runtime, slot_id, cv).corpus_digest

    again = semantic_runtime.add_trial_case(cv, inputs=[_json("x", "a")])
    # A04 rule 1: a case equal to an existing one is that case and keeps its
    # place; A01 rule 4: its first author and time stay.
    assert again.trial_case.trial_case_id == c1
    assert again.corpus_position == 0
    assert again.trial_case.added_at == first.trial_case.added_at
    assert again.trial_case.added_by == first.trial_case.added_by

    corpus = semantic_runtime.get_repair_view(slot_id).corpus
    assert [case.trial_case_id for case in corpus] == [c1, c2, c3]
    # A04 rule 2: the digest is the identity of the id list in corpus order —
    # [c1, c2, c3], not a sorted or set form of it.
    assert _history(semantic_runtime, slot_id, cv).corpus_digest == digest
    assert digest == _corpus_digest([c1, c2, c3])

    # Control: a new case takes the next place and changes the digest, so the
    # unchanged digest above is the equal case, not a digest that never moves.
    c4 = semantic_runtime.add_trial_case(cv, inputs=[_json("x", "d")])
    c4_id = c4.trial_case.trial_case_id
    assert c4_id not in (c1, c2, c3)
    assert c4.corpus_position == 3
    assert _history(semantic_runtime, slot_id, cv).corpus_digest == _corpus_digest(
        [c1, c2, c3, c4_id]
    )
