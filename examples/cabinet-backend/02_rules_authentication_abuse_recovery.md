# State 2 — Cabinet authentication abuse and recovery policy

## Accepted decision A67 — bounded human login abuse and explicit credential recovery

A60, A61, and A66 define the applicable human, agent/service, and synchronization authentication boundaries. This decision closes the abuse, throttling, recovery, and revocation policy for those boundaries without reintroducing a Cabinet-owned local human password store.

### Normative rules

1. VPS human login uses a Cabinet-managed account credential and finite-lived session.
2. Failed VPS login attempts are tracked against both the target account and the request source. One source must not gain an independent full attempt budget for each account, and one account must not gain an independent full attempt budget for each source.
3. After 5 consecutive failed attempts for the relevant account/source abuse context, Cabinet applies progressive delay before accepting another login attempt.
4. After 10 consecutive failed attempts for the relevant abuse context, Cabinet temporarily blocks new login attempts for 15 minutes.
5. A successful authenticated login resets the applicable consecutive-failure counter for that account/session context. Expiry of a temporary block does not erase security audit evidence.
6. Login and recovery responses must not disclose whether a supplied account identifier exists.
7. VPS human-account recovery uses only a recovery channel bound to the account before recovery begins. The baseline recovery proof is control of that pre-bound email channel through a single-use, short-lived recovery token or link.
8. Security questions, knowledge of invoice/project data, and possession of a Cabinet entity identifier are not accepted recovery proof.
9. Successful human-account recovery revokes all active human sessions for that account before a new authenticated session may be established.
10. Ordinary forgotten-password recovery does not automatically revoke `SyncNodeCredential` or agent/service credentials because those identities are separate trust boundaries.
11. When account or device compromise is known or reasonably suspected, affected agent/service and synchronization credentials are revoked or rotated in addition to human-session revocation according to the affected boundary.
12. Machine/service credentials do not have a password-recovery flow. Invalid or replayed credentials are rejected; repeated abnormal authentication failures are throttled; known or suspected credential compromise requires revocation or mandatory rotation and re-enrollment where necessary.
13. Local interactive human access in the accepted single-user baseline continues to rely on the authenticated operating-system session and therefore has no Cabinet-owned local human recovery endpoint.
14. All throttling, temporary-block, recovery, revocation, and rotation decisions emit security audit evidence that does not contain reusable secrets.

### Formal invariants

```text
vps_human_failed_attempts >= 5
-> progressive_delay

vps_human_failed_attempts >= 10
-> login_blocked_for_15_minutes

successful_vps_recovery
-> all_human_sessions_revoked

forgotten_password_recovery
-/> automatic_machine_credential_revocation

known_or_suspected_credential_compromise
-> affected_credential_revoked_or_rotated

local_os_delegated_human_context
-/> Cabinet_local_password_recovery
```

### Required tests

1. Five consecutive failed VPS human-login attempts trigger progressive delay.
2. Ten consecutive failed attempts trigger a 15-minute temporary block and no protected session is created during the block.
3. Attempts distributed across accounts from one abusive source still encounter source-scoped throttling.
4. Attempts distributed across sources against one account still encounter account-scoped throttling.
5. Login and recovery responses are indistinguishable with respect to whether the account identifier exists.
6. A valid recovery token is single-use and rejected after expiry or successful use.
7. Successful recovery invalidates every pre-existing human session for the account.
8. Ordinary password recovery leaves unrelated local-agent/service and sync-node credentials active.
9. Marking the event as account/device compromise revokes or forces rotation of every affected non-human credential selected by the incident scope.
10. Replayed, revoked, or malformed machine/service credentials cannot authorize an operation and repeated failures are throttled.
11. The local single-user interactive flow exposes no Cabinet human password-recovery endpoint.

### Consequence

OQ-008 is resolved. Cabinet has explicit abuse and recovery behavior for the public human boundary and explicit rejection, throttling, rotation, and revocation behavior for machine/service credentials. The local single-user baseline remains free of a second human password system.
