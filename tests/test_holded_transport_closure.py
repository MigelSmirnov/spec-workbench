from __future__ import annotations

import json
from pathlib import Path

from holded_transport_workbench import deterministic_method_scopes, structured_addresses


ROOT = Path(__file__).resolve().parents[1]
CABINET = ROOT / "examples" / "cabinet-backend"


def _load(name: str) -> dict:
    return json.loads((CABINET / name).read_text(encoding="utf-8"))


def test_closed_holded_transport_is_assembled_without_semantic_edits() -> None:
    closure = _load("70_holded_transport_closure.json")
    spec = _load("global_spec.json")

    assert closure["status"] == "closed"
    assert spec["rules"]["holded_transport_backend"] == closure["backend_ir"]
    assert spec["config"]["holded_runtime"]["credential_env"] == "HOLDED_V1_API_KEY"
    assert "base_url_env" not in spec["config"]["holded_runtime"]
    assert "max_recovery_pages" not in spec["config"]["holded_runtime"]


def test_holded_transport_owns_the_deterministic_client_and_wire_date() -> None:
    spec = _load("global_spec.json")

    assert spec["module_functions"]["holded_transport"] == ["holded_wire_date", "HttpxHoldedHttpClient"]
    assert spec["contracts"]["holded_wire_date"] == "(value: date) -> int"
    assert "HttpxHoldedHttpClient" not in spec["module_functions"]["holded_gateway"]
    assert spec["contracts"]["HoldedHttpClient.list_purchases"] == "(self) -> HoldedPurchaseListPage"
    assert spec["contracts"]["HttpxHoldedHttpClient.list_purchases"] == "(self) -> HoldedPurchaseListPage"
    assert spec["models"]["HoldedPurchaseAttemptPayload"]["fields"]["date"] == "int"
    assert spec["models"]["HoldedRemotePurchaseDocument"]["fields"]["document_date"] == "int"


def test_holded_v1_wire_contract_matches_runtime_evidence() -> None:
    backend = _load("70_holded_transport_closure.json")["backend_ir"]
    protocol = backend["protocol"]

    assert protocol["origin"] == "https://api.holded.com"
    assert protocol["credential_header"] == "key"
    assert protocol["create"] == {"method": "POST", "path": "/api/invoicing/v1/documents/purchase"}
    assert protocol["list"] == {"method": "GET", "path": "/api/invoicing/v1/documents/purchase"}
    assert protocol["get"] == {
        "method": "GET",
        "path_template": "/api/invoicing/v1/documents/purchase/{document_id}",
    }
    assert protocol["transport_retries"] == 0
    assert protocol["follow_redirects"] is False
    assert backend["payload"]["subtotal_semantics"] == "net_unit_amount_before_tax"


def test_closed_ir_is_visible_to_notes_and_deterministic_review() -> None:
    assert structured_addresses(CABINET) == {"rules.holded_transport_backend"}
    assert deterministic_method_scopes(CABINET) == {
        "HttpxHoldedHttpClient.__init__",
        "HttpxHoldedHttpClient.create_purchase",
        "HttpxHoldedHttpClient.list_purchases",
        "HttpxHoldedHttpClient.get_purchase",
    }
