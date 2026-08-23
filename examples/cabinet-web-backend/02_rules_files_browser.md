# State 2 — File and browser boundary rules

## Accepted decision A05 — Web ingress stores one bounded non-executable original

### Normative rules

1. M15 authorizes exactly one file upload for one existing Card ID, M05 source
   ID, and expected M03 revision. It cannot create or replace source identity.
2. The first release accepts one original per handoff. Multi-page/multi-image
   invoices must be supplied as one accepted document; additional logical
   sources require an accepted later Card contract rather than filename tricks.
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
7. Stored bytes are immutable under M06 hash. Repeated equal bytes for the same
   Card/source are idempotent; conflicting bytes cannot overwrite accepted
   custody.
8. Retrieval requires authorization for the exact Card/source and returns a
   bounded download response, never filesystem path or storage credential.
9. Successful Web ingress means only Cabinet Web custody. It does not mean
   Card confirmation or local Backend durable acceptance.
10. No server OCR, preview extraction, or receipt-recognition workload is part
    of the ingress path.

### Formal invariants

```text
source_custody_stored
-> handoff_valid AND payload_within_limits
   AND content_type_identified AND content_hash_verified

filename_or_payload_content -/> storage_path_or_executable_structure
source_identifier_known -/> retrieval_authorized
web_custody -/> local_durable_acceptance
```

### Required tests

1. Every unsupported, oversized, empty, malformed, and content/type-mismatched
   upload fails without visible stored custody.
2. Absolute/traversal-like filenames cannot influence storage placement.
3. Equal retry returns one custody result; conflicting bytes do not overwrite.
4. Upload without exact active handoff and expected revision is rejected.
5. Download by guessed Card/source ID without authorization is rejected.
6. Responses and logs disclose no storage path, secret, or executable preview.

### Consequence

The secondary Web page solves byte custody only and does not turn the backend
into a document-processing service.

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
2. Stored script/markup strings render inertly in every Cabinet page.
3. Framing and permissive cross-origin credential use are blocked.
4. Direct access to the private application listener is unavailable externally.
5. Download filenames and media types cannot create inline active content.

### Consequence

The Web helper remains a protected same-origin surface and cannot weaken the
primary ChatGPT/plugin authorization boundary.

