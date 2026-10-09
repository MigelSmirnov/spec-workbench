"""Witness tests for accepted decision A21 (02_rules_installation.md).

The State 0-2 security review is complete: every required category has one
outcome, every APPLICABLE category references an accepted decision, and none
is UNRESOLVED. Each test carries the witness name its Required test declares.

The Factory project supplies the ``semantic_runtime`` pytest fixture. It binds
scenarios to the generated public operations of State 5 — named by their
operation names, with arguments shaped as the State 6 models. A21's Required
tests are not about kernel behaviour: they are about the design gate
(``design_lint --state 2``) run over the specification documents of this case,
which no kernel operation and no fixture capability reaches.

Fixture surface used here: none — both tests skip and name what verifies them.
"""

import pytest


def test_security_review_gate_complete(semantic_runtime):
    """[witness: verification:kernel_a21_security_review_gate_complete]

    A21 Required test 1: `design_lint --state 2` accepts exactly one complete
    review record.
    """
    pytest.skip(
        "capability needed: the State 2 design gate over the specification, not "
        "the kernel — verified by `python tools/design_lint.py "
        "examples/cabinet-kernel --state 2` reporting no security-review finding "
        "(exactly one 'Security review: PERFORMED' record, every category one "
        "outcome, no UNRESOLVED)"
    )


def test_security_references_resolve(semantic_runtime):
    """[witness: verification:kernel_a21_security_references_resolve]

    A21 Required test 2: every reference resolves to an indexed State 2
    decision.
    """
    pytest.skip(
        "capability needed: the State 2 design gate over the specification, not "
        "the kernel — verified by `python tools/design_lint.py "
        "examples/cabinet-kernel --state 2` reporting no "
        "unresolved_security_reference / missing_security_reference finding "
        "(every reference names an indexed accepted State 2 decision)"
    )
