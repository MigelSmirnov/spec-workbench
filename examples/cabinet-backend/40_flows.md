# State 4 — Cabinet Backend key system flows

## Status

State 4 is in progress. This document records reviewed end-to-end flows using explicit State 3 module and candidate-capability references. The flow descriptions do not finalize State 5 public contracts.

---

## `flow:synchronize_invoice_to_local_archive`

### Trigger

A synchronization cycle initiated by Local Cabinet Backend observes one exact VPS Cabinet invoice work package that is eligible to be transferred toward local durable custody.

### Boundary

The transport boundary enters through `module:synchronization`. Transport delivery is not durable acceptance. Local archive acceptance belongs only to `module:durable_archive`.

The flow may use the candidate State 3 needs `capability:synchronization.synchronize_invoice_work`, `capability:durable_archive.accept_transfer_manifest`, and `capability:durable_archive.verify_durable_acceptance`. These names remain candidate capabilities until State 5.

### Steps

1. `module:synchronization` authenticates and performs the accepted outbound synchronization protocol using the synchronization-only node identity; local service or human authorization is not substituted for that credential boundary.
2. `module:synchronization` receives or constructs the exact transfer package and preserves its transfer identity, hashes, and delivery/reconciliation evidence without claiming business acceptance.
3. The package required set is presented to `module:durable_archive` for local acceptance under the accepted manifest, source-integrity, duplicate, quarantine, and atomic-visibility rules.
4. `module:durable_archive` validates the exact immutable Invoice Card revision and required source evidence, then either accepts the required set atomically, recognizes an already accepted idempotent transfer, or records the accepted failure/quarantine outcome.
5. Only after `module:durable_archive` proves durable acceptance may synchronization record or transmit the corresponding acceptance receipt. A successful network delivery by itself never creates an accepted archive fact.
6. If the transport outcome is unknown, `module:synchronization` reconciles by read/status evidence and must not create a second logical transfer merely because the previous network result was ambiguous.

### Outcomes

Successful observable outcomes are:

- the exact invoice revision and its required source set are durably accepted and visible in the local archive; or
- the transfer is recognized as already accepted with the same accepted identity/evidence.

Non-success terminal or review outcomes include:

- rejected or unsupported package content;
- quarantine requiring explicit resolution;
- duplicate-candidate review where State 2 requires review rather than silent merge;
- missing or invalid required source evidence;
- transport outcome remaining unknown until reconciliation completes.

The observable result must preserve the distinction between transport delivery state and archive acceptance state.

### Errors

`module:synchronization` owns translation of transport/authentication/retry/reconciliation failures into synchronization outcomes. It must not translate a transport success into archive acceptance.

`module:durable_archive` owns archive-validation, integrity, duplicate, idempotency, quarantine, and atomic-acceptance failures. Persistence adapters may report technical failures but must not decide those business outcomes.

If an error reveals that the package lacks data required by an already accepted State 1 or State 2 decision, the repair belongs to that earlier state rather than being hidden inside this flow.

### State 4 review notes

This flow deliberately crosses only the synchronization and durable-archive responsibility boundary. It does not include Registry catalogue publication, PresuPro analysis, Holded publication, retention release, or general local-agent operations; those require separate State 4 flows because they have different triggers, owners, errors, and observable outcomes.
