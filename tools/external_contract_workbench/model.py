from __future__ import annotations


SCHEMA = "spec_workbench_external_contract_evidence.v1"
REPORT_SCHEMA = "spec_workbench_external_contract_coverage.v1"
AUTHORITIES = {"observed_runtime", "official_documentation", "combined"}
STATUSES = {"active", "superseded"}
ROOT_FIELDS = {"schema_version", "status", "contracts"}
CONTRACT_FIELDS = {
    "id", "status", "authority", "subject", "verified_by", "verified_at", "evidence",
    "bindings", "modules", "supersedes", "superseded_by",
}
SUBJECT_FIELDS = {"system", "api_family", "environment"}
EVIDENCE_FIELDS = {"artifact", "sha256", "run_id", "result"}
BINDING_FIELDS = {"address", "value_sha256"}


class ExternalContractEvidenceError(ValueError):
    """External-contract evidence cannot be loaded safely."""
