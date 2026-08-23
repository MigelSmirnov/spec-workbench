# State 2 — Cabinet Web Backend rule-set status

## Accepted decision A16 — first-release capability catalogue is closed

### Normative rules

The first-release application capability catalogue is:

```text
human read/proposal
  provider.search
  project.list
  project.summary
  invoice.search
  invoice.get
  invoice.find_duplicates
  invoice.prepare_draft
  invoice.validate
  estimate.validate
  shopping_list.derive
  registry_catalogue.current

browser source retrieval
  source.download

human effects
  invoice.create_draft
  invoice.update_draft
  invoice.confirm
  invoice.record_payment
  invoice.attach_source_metadata
  invoice.archive
  project.attach_estimate
  shopping_list.save
  source_upload_handoff.issue
  vps_working_set.release

local Backend synchronization
  synchronization.observe_compatibility
  invoice_work.discover
  invoice_package.pull
  invoice_transfer.receipt
  invoice_transfer.reconcile
  registry_catalogue.publish

protected operator
  principal.enroll
  principal.grant_capability
  credential.rotate
  credential.revoke
  backup.verify_restore
```

1. Each capability has one fixed semantic operation and typed input/output in
   later states. Dotted names are stable catalogue values, not module or
   function names.
2. `invoice.prepare_draft`, `invoice.validate`, `estimate.validate`, and
   `shopping_list.derive` create proposals/projections only and are read-like
   for authorization/audit; they do not persist a Card or artifact.
3. Human effects require A03 authorization and A04 idempotency. Exact
   confirmation requirements remain governed by A02.
4. Synchronization capabilities are available only to the scoped active M17
   local node. Operator capabilities are absent from ChatGPT, browser, and
   synchronization tool catalogues.
5. `principal.grant_capability` is callable only at the protected
   composition/operator boundary. It provisions one exact A03 grant and is
   never exposed as an ordinary plugin, browser, or synchronization tool.
6. `source_upload_handoff.issue` creates M15; original bytes enter only through
   A05/A06 Web ingress. It is not a generic file capability.
7. No arbitrary delete, SQL, filesystem, Git, shell, URL fetch, generic proxy,
   dynamic tool, or `cabinet_backend` operation capability exists.
8. Adding or broadening a capability requires returning to the earliest
   affected State 0–2 decision and security review before contracts change.

### Formal invariants

```text
requested_capability in first_release_capability_catalogue

grantable(channel, requested_capability)
<-> exists one row in rules.capability_catalogue.grantable
    with row.channel = channel
    and row.capability = requested_capability

human_effect
-> A03_authorized AND A04_idempotent

operator_capability -/> plugin_or_browser_or_sync_catalogue
principal.grant_capability -> A03_protected_grant_provisioning
unknown_capability -> reject_without_dispatch
```

The machine-readable single home for the capability/channel/semantic-operation
correspondence is `rules.capability_catalogue`. The protected-operator entries
are catalogue members but are deliberately outside `grantable` and cannot be
provisioned to plugin, browser, or local-node credentials.

### Required tests

1. Every listed capability maps to exactly one semantic operation class.
2. Unknown and prefix/suffix-confused capability names are rejected.
3. Proposal capabilities cause no durable Card/artifact mutation.
4. Human, local-node, and operator capability sets cannot be substituted.
5. No exposed capability accepts arbitrary path, URL, query, command, or tool
   selection.

### Consequence

State 3 may derive ownership from an explicit product capability surface rather
than inventing modules around a generic MCP dispatcher.

## State 2 coverage review

| State 1 models | Governing decisions |
| --- | --- |
| M01–M04 actor, principal, revision, validation | A01–A04, A11, A12, A16 |
| M05–M06 logical source and exact bytes | A01, A05, A06, A08, A10, A13 |
| M07–M13 Cards and project artifacts | A01–A04, A08, A09, A16 |
| M14–M16 custody, handoff, Cabinet effect | A04–A06, A10–A13, A16 |
| M17 local node | A03, A08, A09, A11, A13, A16 |
| M18–M20 Registry snapshots/replica | A09, A12, A13 |
| M21–M23 Invoice manifest/issuance/receipt | A04, A08, A10–A13 |
| M24–M25 catalogue delivery/acknowledgement | A04, A09, A11–A13 |
| M26 connection observation | A08, A11, A13 |
| M27 working-set observation | A08, A10, A13 |
| M28 synchronization conflict | A01, A04, A08, A10 |
| M29 Card object assignment observation | A01, A02, A08, A09, A12 |

## State 2 readiness assessment

- canonical Card and source identity rules are closed;
- ChatGPT proposal, confirmation, capability, and effect semantics are closed;
- file type/size/path/execution/storage/retrieval rules are separate and closed;
- browser origin, CSRF, output encoding, and private listener policy are closed;
- Invoice pull, receipt, unknown outcome, conflict, and Registry publication
  transitions are closed;
- manual safe release, backups, restore checks, operational limits, credential
  lifecycle, and dependency policy are closed;
- all nine mandatory security categories are `APPLICABLE` with accepted owners;
- no open State 2 question remains.

Deterministic gate result:

```text
accepted decisions       16
resolved references      30
errors                     0
warnings                   0
open questions             0
security categories        9/9 APPLICABLE
STATE 2                  PASS
```

The external `cabinet_backend` wire contract remains subject to the explicit
pre-State-6 and pre-Stage-9 refresh recorded in
`STATE2_EVIDENCE_CHECKPOINT_2026-08-23.md`. That obligation does not authorize a
generic interim API and does not leave State 2 product policy unresolved.
