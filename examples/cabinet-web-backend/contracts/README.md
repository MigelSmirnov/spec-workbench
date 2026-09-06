# Transitional canonical read contract

`legacy_invoice_snapshot_v1.schema.json` defines the bounded read-only input
from today's Cabinet_web. Cabinet Flow is still planned; it is not a runtime
dependency of this adapter. The schema embeds the unchanged product
InvoiceCardV1 schema, copied deterministically from the pinned source revision.
It does not define another Invoice product model.

The offline emitter is `../tools/emit_legacy_invoice_snapshot.py`. It reads only
Git objects from an explicit full commit. The trusted repository, accepted
commit, and byte bound are operator inputs, not fields supplied by an HTTP or
MCP caller. No repository code, hook, working-tree file, or request bridge is
executed. The source-only recovery audit must cover the entire committed Invoice
inventory and match every Card's raw hash and every recovered original's hash
and size. An unknown association or absent audited Card fails explicitly.

```bash
python examples/cabinet-web-backend/tools/emit_legacy_invoice_snapshot.py \
  --repository /path/to/trusted/Cabinet_web \
  --commit FULL_ACCEPTED_COMMIT \
  --audit-path docs/04-migrations/SOURCE_RECOVERY_20260906.json \
  --max-object-bytes OPERATOR_OBJECT_BOUND \
  --output /path/outside/source/to/new-snapshot
```

Output is an immutable `bundle/snapshot.json` plus private
`bundle/objects/<raw-sha256>` objects. Output must be outside the source
repository and must not already exist. The emitter verifies each written object
by re-reading it. A fresh export of the same commit has identical JSON and object
bytes: no current timestamp or absolute local path enters content identity.

The snapshot's raw SHA-256 is computed over the exact `snapshot.json` bytes,
including the final newline. Canonical Card hashes retain the existing product
`sha256:` prefix and the exact sorted, compact UTF-8 JSON recipe from
`invoice_service.content_hash`. They are distinct from raw Card-file hashes.
Source-set hashes apply that same canonical encoding to the complete
`source_set` object. Each file's `content_id` is its prefixed raw byte hash;
it is distinct from the Card-scoped logical `source_id`. Ordinals preserve
accepted audit order, not inferred page numbering. Duplicate content identities
inside one audited set fail instead of silently changing membership.

An empty observed file list is representable so missing sources are visible;
it is not an accepted complete source set. The recovery corpus is JPEG/PDF.
The emitter's signature check recognizes that audited corpus; it does not
replace full runtime A05 validation or narrow the general ingress catalogue.
Unassociated recovered receipts/orders are verified and counted but are not
invented as Invoice associations or placed in the Invoice source package.

Raw capture evidence is retained byte-for-byte, including malformed evidence.
The capture observation distinguishes missing, malformed/invalid, stale,
mismatched, incomplete, and mechanically verified legacy evidence. Verification
checks the existing version, Card/source identity, product hash, positive integer
counts, and current line count. It does not produce a new capture proof, bind an
old proof to new source membership, or assert page/document completeness.

This snapshot is **not** the Backend transfer wire format, a source-custody
receipt, a transfer admission, or a durable local acceptance. A receiver must
verify its configured origin and expected snapshot hash, every referenced
object, canonical Card hash, source-set hash, exact membership and authorization
before consuming it. Caller-provided origin/hash fields alone are not trust.
`SOURCE_REGISTRATION_CONTRACT_20260906.md` owns the operations and the remaining
State 1–9 propagation; do not send this new wrapper directly to the old Backend
parser or mark its emission as a successful synchronization.

Validation:

```bash
pytest -q examples/cabinet-web-backend/tests/test_legacy_invoice_snapshot.py
```
