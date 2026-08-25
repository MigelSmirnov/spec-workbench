# External contract evidence

External wire facts are not product requirements and must not be regenerated
from plausibility. A value such as an API origin, credential-header name,
versioned endpoint, response-field name, or financial field meaning may be
well-typed and still be factually wrong.

Workbench therefore distinguishes two independent closure conditions:

1. implementation closure: a supported backend owns deterministic lowering;
2. evidence closure: external facts have content-addressed provenance.

Evidence closure is a Workbench authoring and admission responsibility. It does
not add a section to `global_spec.json` and does not require Factory to parse or
validate evidence.

## Artifact

Projects that contain empirically or documentarily established external facts
record them in `70_external_contract_evidence.json` using schema
`spec_workbench_external_contract_evidence.v1`.
Every post-contract closure that depends on such facts lists their stable ids in
`external_contract_evidence_ids`. Consequently, deleting the manifest cannot
turn a required check into `NOT_APPLICABLE`.

Each contract records:

- stable id and lifecycle status (`active` or `superseded`);
- authority (`observed_runtime`, `official_documentation`, or `combined`) and
  the reviewer or controlled-run owner in `verified_by`;
- external system, API family, and tested environment scope;
- UTC verification time;
- relative evidence artifact, its SHA-256, run id, and result;
- bindings from exact `config.*`, `models.*`, or `rules.*` addresses to the
  SHA-256 of their canonical JSON values;
- assembled modules whose review packets require this evidence;
- reciprocal supersession links.

The evidence artifact must be committed inside the case directory. Store only
sanitized observations. Credential values, authorization headers containing a
credential, cookies, and reusable remote identifiers must not be recorded.
Names of credential slots and header fields are allowed because they are the
contract being verified.

## Invariants

- Active bindings must resolve and their canonical value hashes must match.
- Evidence files must exist inside the project and match their recorded hashes.
- One address cannot have two active evidence owners.
- Changing an active value without a new verified contract is a blocking
  `verified_value_changed`, even when the new value is structurally valid.
- A superseded record remains content-addressed but no longer constrains the
  current assembled value. Supersession must be reciprocal; history is not
  edited in place.
- A mutation probe is never rerun automatically. It requires its own explicit
  authorization; the Workbench consumes the already-recorded result.

Run:

```bash
python tools/design_external_contracts.py examples/<case>
python tools/design_assembly.py examples/<case> --check external_contracts
```

Assembly and Stage 9 admission fail before export when evidence is stale or
invalid. Module review slices include active evidence only for the modules named
by the evidence record.
