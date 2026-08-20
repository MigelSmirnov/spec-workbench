from __future__ import annotations

from pathlib import Path

from box_language_audit import audit_language, current_implementations


ROOT = Path(__file__).resolve().parents[1]
LANGUAGE = ROOT / "experiments" / "cabinet-vault" / "box_language_v0.yaml"


def test_current_box_compilers_match_declared_language_exactly():
    report = audit_language(LANGUAGE, root=ROOT)

    assert report.status == "pass"
    assert report.findings == ()
    assert set(report.checked_tools) == {"box_derivability", "box_composition"}
    assert len(report.checked_rules) == 15


def test_hidden_implementation_rule_blocks_audit():
    implementations = current_implementations()
    implementations = {
        **implementations,
        "box_derivability": frozenset(
            {*implementations["box_derivability"], "BXL-HIDDEN-999"}
        ),
    }

    report = audit_language(LANGUAGE, root=ROOT, implementations=implementations)

    assert report.status == "block"
    assert any(
        finding.code == "HIDDEN_IMPLEMENTATION_RULE"
        and finding.subject == "box_derivability:BXL-HIDDEN-999"
        for finding in report.findings
    )


def test_declared_rule_missing_from_compiler_blocks_audit():
    implementations = current_implementations()
    implementations = {
        **implementations,
        "box_composition": frozenset(
            rule
            for rule in implementations["box_composition"]
            if rule != "BXL-COMPOSE-005"
        ),
    }

    report = audit_language(LANGUAGE, root=ROOT, implementations=implementations)

    assert report.status == "block"
    assert any(
        finding.code == "DECLARED_RULE_NOT_IMPLEMENTED"
        and finding.subject == "box_composition:BXL-COMPOSE-005"
        for finding in report.findings
    )


def test_compilation_artifacts_expose_applied_language_rules():
    from box_composition import IMPLEMENTED_BOX_LANGUAGE_RULES as composition_rules
    from box_composition import compile_composition
    from box_derivability import IMPLEMENTED_BOX_LANGUAGE_RULES as derivability_rules
    from box_derivability import derive_capability_mapping

    source = {
        "schemas": {
            "Empty": {"fields": {}},
            "Source": {
                "fields": {
                    "id": {
                        "type": "str",
                        "semantic": "thing.identity",
                        "authority": "thing.authority",
                    }
                }
            },
        },
        "capabilities": {"thing.get": {"input": "Empty", "output": "Source"}},
    }
    target = {
        "schemas": {
            "Target": {
                "fields": {
                    "thing_id": {
                        "type": "str",
                        "semantic": "thing.identity",
                        "authority": "thing.authority",
                        "mapping": "exact",
                    }
                }
            },
            "Result": {"fields": {}},
        },
        "capabilities": {"thing.accept": {"input": "Target", "output": "Result"}},
    }

    derivation = derive_capability_mapping(source, "thing.get", target, "thing.accept")
    composition = compile_composition(source, "thing.get", target, "thing.accept")

    assert derivation.language_rules == tuple(sorted(derivability_rules))
    assert composition.language_rules == tuple(sorted(composition_rules))
