# State 2 — File and browser boundary rules

## Accepted decision A05 — immutable original files preserve their logical source association

### Normative rules

1. Under D0-009, the first-version original ingress belongs to Cabinet Flow's
   Syncthing Inbox. Cabinet Flow accepts and associates immutable originals;
   this service verifies working copies for the exact canonical Card/source
   and revision. M15/A06 describe a retained legacy browser handoff, not the
   first-version source authority or a bypass of the canonical owner.
2. Under D0-012, one logical Invoice source may contain several original files.
   Preserve the existing logical source ID and accepted ordered membership;
   give every distinct file a separate content identity. Photographs are
   originals; do not replace them with a synthesized PDF. A file ordinal is
   not a page count. Partial or alternate-page photographs do not prove
   document completeness.
3. Accepted content types are a closed catalogue: PDF, JPEG, PNG, WebP, HEIC,
   and HEIF. Extension and caller-declared media type alone are insufficient;
   bounded content identification must agree with an accepted type.
4. The exact limits in A13 apply before parsing or durable publication.
   Oversized, empty, malformed, type-mismatched, or unsupported content is
   rejected without M14 `stored` state.
5. Files are untrusted data and never executable authority. Cabinet Web does
   not execute, render as active HTML, import macros, or allow contents to
   choose commands, prompts, templates, queries, or storage paths.
6. Original filename is display/provenance only. The server chooses every
   storage key and keeps bytes outside publicly served and source-code roots.
7. Stored bytes are immutable under M06 hash. Equal retry of the exact scoped
   registration has one logical result. Conflicting bytes cannot overwrite
   an accepted content identity. Changed source membership creates another
   immutable observation, never an edit of an issued manifest or receipt.
   Complete set custody requires every declared file to be verifiable;
   partial publication remains pending or failed with exact recovery evidence.
8. Retrieval requires authorization for the exact Card/source, accepted set,
   and selected file; it returns a bounded download response, never a filesystem
   path or storage credential. A source-only query cannot silently select the
   first photograph from a multi-file document.
9. Registration is allowed for an already confirmed canonical Invoice and
   changes custody only. It does not edit Card JSON, create a Card revision,
   reopen a draft, re-confirm, or alter line-capture proof. It does not mean
   complete capture, ready delivery, or local Backend durable acceptance.
10. No server OCR, preview extraction, or receipt-recognition workload is part
    of the ingress path.

### Formal invariants

```text
source_custody_stored
-> canonical_association_verified AND exact_scope_authorized
   AND every_declared_file_within_limits
   AND every_declared_file_type_identified AND every_declared_file_hash_verified

custody_registration -> canonical_card_before = canonical_card_after
custody_registration -> capture_evidence_before = capture_evidence_after
file_count -/> page_count OR document_completeness
source_set_changed -> new_immutable_observation

filename_or_payload_content -/> storage_path_or_executable_structure
source_identifier_known -/> retrieval_authorized
web_custody -/> capture_completeness OR local_durable_acceptance
```

### Required tests

1. Every unsupported, oversized, empty, malformed, and content/type-mismatched
   [witness: verification:witness_A05]
   [witness: verification:streaming_source_download_behavior]
   upload fails without visible stored custody.
2. Absolute/traversal-like filenames cannot influence storage placement.
3. Equal retry returns one custody result; conflicting bytes do not overwrite.
4. Registration without canonical association, exact revision, or scope
   authorization is rejected; a legacy handoff is no substitute for those facts.
5. Download by guessed Card/source/set/file without authorization is rejected.
6. Responses and logs disclose no storage path, secret, or executable preview.

### Consequence

D0-012 supersedes the former single-file restriction. The source owner accepts
originals and document membership; this service owns working-copy verification
and delivery custody. The typed multi-file closure and canonical-owner ingress
must be propagated before assembly/admission; the old single-content M14 and
browser-only implementation do not implement this correction. The contract
and its open propagation ledger are in SOURCE_REGISTRATION_CONTRACT_20260906.md.

## Accepted decision A06 — upload handoffs are short-lived and single-use

### Normative rules

1. M15 is issued only after the authorized owner selects the exact Card/source
   and current revision through ChatGPT or the protected Web application.
2. A handoff is usable only before its configured expiry, by the intended human
   boundary, for its exact target and one payload.
3. Successful custody commit atomically changes `issued -> consumed`. Concurrent
   submissions cannot consume the same handoff twice.
4. Expired, revoked, consumed, malformed, or target-mismatched handoffs fail
   closed and cannot be refreshed implicitly.
5. The presented bearer value is returned only for use in the protected upload
   URL/form, is never stored in plaintext, and is absent from logs, analytics,
   referrers, Card data, filenames, and synchronization packages.
6. Issuing another handoff creates another M15 entity and does not mutate an
   expired or revoked handoff.

### Formal invariants

```text
handoff_consumed -> prior_status = issued AND now < expires_at
count(successful_consumption per handoff_id) <= 1
expired_or_revoked_or_consumed -/> upload_authority
```

### Required tests

1. Expired, consumed, revoked, and wrong-target handoffs are rejected.
   [witness: verification:witness_A06]
2. Concurrent submissions produce at most one successful consumption.
3. A failed payload validation does not falsely consume the handoff unless the
   explicit abuse policy revokes it.
4. Reusable bearer material never appears in durable business data or logs.

### Consequence

The upload page can remain secondary and narrowly scoped without inheriting a
broad authenticated file-manager session.

## Accepted decision A07 — browser output and mutation requests remain same-origin

### Normative rules

1. Public TLS terminates at the existing VPS edge; the application listener is
   private behind it. No unrestricted backend port is public.
2. The first release retains one nginx Basic Auth human boundary for secondary
   Web pages. Basic Auth is not plugin or local-node authentication.
3. State-changing browser requests require accepted same-origin enforcement and
   an unguessable CSRF value bound to the current protected browser context.
   The value is not a session: it is derived for the authenticated owner and
   the exact upload handoff (M164) with the credential pepper, fetched by the
   upload page from the same-origin CSRF operation, and presented in both a
   request header and the form; the backend recomputes it and never stores it.
   The owner identity itself is the TrustedEdge assertion the private nginx
   hop injects after Basic Auth (A03 rule 2); no browser credential is
   authenticated by the application.
4. Cross-origin credentialed requests are denied. The accepted Web application
   needs no permissive CORS mode.
5. All Card/source/user strings are encoded as text in HTML. No stored value may
   become raw markup, script, style, event handler, URL scheme, or template
   structure.
6. Security headers restrict framing, active content, referrer disclosure, MIME
   sniffing, and transport downgrade. Source downloads use non-executable
   disposition and the verified media type.
7. Browser state and hidden controls never authorize an entity or capability.
8. Authentication failures are bounded by A11 abuse controls and reveal no
   distinction between unknown and disabled principals.

### Formal invariants

```text
browser_mutation
-> authenticated_owner AND same_origin AND valid_csrf

stored_or_external_text -/> active_browser_content
browser_state -/> authorization_authority
```

### Required tests

1. Cross-origin and missing/invalid CSRF mutation requests fail.
   [witness: verification:witness_A07]
2. Stored script/markup strings render inertly in every Cabinet page.
3. Framing and permissive cross-origin credential use are blocked.
4. Direct access to the private application listener is unavailable externally.
5. Download filenames and media types cannot create inline active content.

### Consequence

The Web helper remains a protected same-origin surface and cannot weaken the
primary ChatGPT/plugin authorization boundary.

