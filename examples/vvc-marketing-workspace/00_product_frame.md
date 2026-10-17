# State 0 — VVC Marketing Workspace

Status: draft for owner review; not accepted or closed.
Created: 2026-10-17.
Updated: 2026-10-17 — owner selected text/photos, deferred voice processing, and required extensible integrations.
Project: `vvc-marketing-workspace`.
Canonical ref: `agent/vvc-marketing-workspace`.
Owner: Vital Vibe Construction.

## 1. Product goal

Provide the owner with a working environment for maintaining the company's Facebook presence, managing Meta advertising, and handling customer enquiries in WhatsApp Business through a personal ChatGPT plugin backed by a service on the owner's VPS.

The value is reduced manual work and controlled completion of real actions. Reporting is supporting evidence, not the primary product. A tool listing or an optimistic response without a verified external result is not a completed action.

The owner is not confident in Spanish. The environment must support understanding a customer's Spanish message, discussing a response in Russian, reviewing the proposed Spanish reply with its Russian meaning, and sending the response after the owner decides to send it.

## 2. Evidence and decision status

### Confirmed by the owner in the initiating conversation

- This is a new, separate project in Spec Workbench; it is not Cabinet Kernel or Cabinet Web Backend.
- The runtime is intended for the owner's existing VPS, where the company website already runs.
- Development is managed through GitHub.
- The immediate priorities are Facebook account maintenance, Meta advertising, and WhatsApp Business integration.
- The working WhatsApp number currently uses the WhatsApp Business application on a phone.
- First-version customer-message scope is text and photographs. The owner listens to voice messages on the phone; automatic voice transcription is excluded from the first version (owner decision, 2026-10-17).
- Customer enquiries are expected through WhatsApp; the owner wants to discuss them and their replies with the assistant.
- A personal plugin connecting ChatGPT to the owner's service is an intended interaction surface.
- The server has two first-version machine clients: the assistant in ChatGPT and a local agent such as Codex. Product decisions are discussed with the owner in chat (owner decision, 2026-10-17). These are two client identities, not two independent owners.
- A phone-accessible red button must block outbound effectful actions initiated by either ChatGPT or the local agent, while preserving the website and receipt of enquiries (owner decision, 2026-10-17). This is an automation freeze, not VPS shutdown or a request to stop already-running Meta advertising.
- Reddit is a possible later direction; the owner deferred its format and priority.
- Login to Meta for Developers is currently unavailable to the owner. Whether a suitable Meta app exists is unknown.
- The owner explicitly requested consideration of VPS requirements and security before implementation.
- ChatGPT and WhatsApp on the phone are sufficient for first-version daily work; no separate enquiry dashboard is required. The phone emergency-stop control remains a separate small owner-facing surface (owner decision, 2026-10-17).
- WhatsApp is the owner's selected channel for new-enquiry and failure notifications (owner decision, 2026-10-17). Exact delivery feasibility, recipient and outage behaviour remain to be designed.
- Only the owner may connect integrations, approve updates or change permissions (owner decision, 2026-10-17). Machine clients may prepare or perform specifically authorized work, not grant themselves administrative authority.
- The server does not call AI/model-provider APIs for translation, drafting, inference or other processing. AI work stays in the ChatGPT or local-agent client under its existing access (owner decision, 2026-10-17). No server-side model API credentials, model gateway or model-serving component is in scope. The service interface used by the two clients and the Meta/WhatsApp APIs remain required integration boundaries.
- The owner prefers simple storage and questioned the need for a database or a large conversation archive. The owner has not requested a full CRM or approved permanent archiving of all conversations and photographs.
- The question about recurring service costs needs explanation before a budget can be selected; no monthly budget has been approved.
- Integration extensibility is required: the architecture must allow separately developed integration modules or adapters (owner decision, 2026-10-17). This decision does not by itself include Instagram or Reddit in the first release.
- Python is the implementation language for the VPS service and integration adapters (owner decision, 2026-10-17). The Python version, framework and dependencies remain to be selected.

### Existing infrastructure evidence; not a current server audit

The website repository is `MigelSmirnov/Vital-Vibe-Constructions`.
Its September deployment report describes public nginx/TLS in front of a private Caddy site container and records unresolved host-hardening checks.
The owner confirms that the website is already on the VPS.
Actual resources, listeners, host access, recovery access, updates, backups and certificate renewal must be inspected before deployment.

The owner referred to the server as "OHL" and mentioned DonDominio. Provider, registrar and DNS-management roles have not been verified; do not silently reinterpret these names.

### Proposed first-version boundaries, pending owner review

- One owner and the company's explicitly connected assets; no agency or multi-customer product.
- Initial external changes are reviewed by the owner before execution.
- Advertising is prepared paused; enabling it is a separate decision.
- Messages are drafted and reviewed before sending; unattended customer replies are outside the initial version.
- The existing phone workflow and company website should be preserved. A phone-number migration is not implicitly authorized.
- Database, framework, container strategy, authentication implementation, resource sizing and deployment method are not selected by this State 0.

## 3. Actors

- Owner: reads enquiries, supplies business facts, edits content, approves or refuses external actions, and manages access.
- Assistant in ChatGPT: one machine client; discusses decisions with the owner, explains retrieved data and proposes content or actions. It is not the source of authority for spending, sending or changing permissions.
- Local agent such as Codex: a second machine client of the same service. It acts only under its own authorized scope; its access does not make it an owner or give it unrestricted host-administration authority.
- Owner on the phone: the human control actor for the emergency-stop surface, separate from both machine clients. The selected scope is an outbound-effect freeze with website and inbound enquiries preserved; authentication and recovery details remain open.
- Customer: sends text and potentially media through WhatsApp. Customer content is untrusted input, not an administrative instruction.
- VPS service: receives integration events, retains the agreed working records, exposes authorized product actions and reports external outcomes.
- Meta services: authoritative source of actual advertising, publication and WhatsApp-message outcomes within granted permissions.
- Developer/deployer: changes reviewed code and deploys releases; development access is distinct from authority to send a message or launch advertising.

## 4. Product actions and observable outcomes

| Owner action | Inputs | Observable result | Failure or uncertainty |
| --- | --- | --- | --- |
| Access from either machine client | Owner-authorized ChatGPT or local-agent connection | Account-scoped product state and allowed capabilities; recorded requests identify the initiating client | An absent, revoked or insufficient client grant is reported as a refusal, not substituted by the other client's authority |
| Inspect connected assets | Authorized connection and selected company assets | Identified accessible assets and observed permissions | Missing, expired or insufficient access is explicit; no inferred connection |
| Use a supported integration | Owner-selected, installed integration and authorized external account | Its available actions and required permissions are visible; results identify the integration and account | Missing, disabled, incompatible or unsupported capabilities are reported explicitly; another account or provider is not silently substituted |
| Prepare a Facebook publication | Owner's brief and permitted company materials | Editable proposed content and selected destination | Missing facts or unsupported media prevent a ready-to-publish claim |
| Publish approved content | Owner's decision on exact content and destination | External publication identity and verified status | Rejection is shown; an uncertain submission remains uncertain |
| Prepare Meta advertising | Goal, creative, audience, destination and budget supplied or reviewed by owner | Paused campaign structure with verified objects and a comparison against requested settings | Partial creation, rejected settings and changed defaults are individually reported |
| Launch or change advertising | Reviewed target objects and exact proposed change | Verified external status or budget change | No claim of success on tool acknowledgement alone; ambiguous outcome is surfaced |
| Receive an enquiry | Authorized WhatsApp event | Durable enquiry and conversation visible to the owner | Invalid events are refused; receipt, storage or delivery failures are observable to the operator |
| Understand an enquiry | Selected original text messages and available customer photographs | Original text, Russian explanation and identified missing business facts, with access to the selected photographs | Unknown meaning or unavailable attachments are stated, not invented |
| View enquiry photographs | Selected conversation and its received photographs | Photographs associated with their source messages and available for owner/assistant review through authorized access | Missing, unsupported or inaccessible photographs are explicitly identified; no fabricated image description |
| Prepare a customer response | Conversation, owner's instructions and known business facts | Editable Spanish draft and Russian meaning | Missing price, availability, scope or terms remain explicit questions |
| Send an approved response | Exact recipient, conversation and owner-reviewed text | Message identity and separately observed delivery state | API rejection, unknown submission and delivery failure remain distinct |
| Track an enquiry | Owner's assessment and supported conversation facts | Current status and history of what changed | The system does not infer a signed contract, payment or qualified lead from a click |
| Inspect an action or recover after failure | Recorded action and external evidence | Known applied, refused, partial or unresolved result | An interrupted action is not blindly repeated and not relabelled successful |
| Freeze outbound automation from the phone | Authenticated owner's emergency-stop instruction | New effectful submissions from either machine client are blocked; website and inbound enquiry receipt remain available; the control shows the recorded stop state | An unreachable or failing control is not reported as stopped; already-submitted external requests retain their actual or uncertain outcome |
| Revoke integration access | Owner's revocation decision | Product stops using the revoked authority and reports its state | External revocation that cannot be verified is reported as unresolved |

Publication, advertising and WhatsApp operations are conditional on each external system granting the necessary access. This table is a product promise inventory, not an API contract or implementation algorithm.

## 5. Inputs, outputs and persistent facts

Inputs include the owner's instructions, authorized asset selections, business descriptions, approved photographs and texts, platform observations, and customer messages.
First-version attachments are customer photographs, associated with their source messages and conversation. Supported image formats, size limits, retention and protected access remain to be designed.
Voice messages remain handled by the owner in the phone application. The first version does not promise voice transcription, translation or audio archiving; the owner may supply a text summary for discussion.

Outputs include retrieved observations, bilingual drafts, approval previews, externally created object identities, observed external statuses, enquiry status histories and operator-visible failures.

Persistent facts needed by the product:
- owner identity and distinct ChatGPT/local-agent connection identities, allowed asset scope and access status;
- conversation events and participant/external message identities needed for the agreed working context and duplicate/outcome checks; the extent and retention of message bodies remain open;
- received photographs needed for current enquiry work and their association with the source conversation and message, subject to the retention decision; permanent photo archiving is not assumed;
- enquiry assessments and owner-entered business facts;
- drafts and the exact version considered by the owner;
- approval/refusal decisions and the external action they concern;
- action attempts, partial outcomes, external evidence and unresolved submissions;
- credential references and lifecycle records, separate from ordinary business data;
- emergency-stop state and owner stop/resume decisions, with attributable action outcomes;
- release identity and operational recovery records.

Exact models, identifiers, status vocabularies, schema fields and retention durations belong to later design work or the open questions below.

### Minimal-storage proposal, not yet a selected database design

Keep enough durable service state for separate client access, revocation, the emergency freeze, owner decisions, external object/message identities, action outcomes and unresolved attempts. This need exists even without a full conversation archive: a restart must not turn unknown submissions into safe-to-repeat work or erase the evidence of authority.
Use only the message context and photographs needed for current owner-assisted enquiry work; do not assume permanent replication of the phone's entire WhatsApp history. Exact retention, deletion and backup treatment must be resolved before real customer data is collected.
The choice of SQLite, another database or a different durable store belongs to later design. This proposal explains the need for persistence; it is not owner approval of a schema, library or complete archive.

## 6. External systems and product boundaries

- ChatGPT personal plugin / remote MCP: one authenticated machine-client boundary; availability in the owner's account remains to be tested.
- Local agent such as Codex: the second authenticated machine-client boundary. The local machine is outside the VPS service trust boundary; an authenticated client is not assumed to be uncompromised.
- Phone emergency control: owner-facing authority independent of both machine clients. The accepted scope is an outbound-effect freeze; authentication, reachability and recovery remain to be designed.
- Meta Marketing API: advertisement operations on explicitly authorized company assets.
- Facebook publication APIs: required page identity and permissions remain to be verified separately from advertising permissions.
- WhatsApp Business Platform: message delivery and inbound events; working-number onboarding and phone/API coexistence remain unresolved.
- Existing website: neighbouring production workload, not part of the marketing service's writable data.
- GitHub: source and review history. This specification repository is public; actual customer data, credentials and private operational evidence are not project files.
- VPS provider and domain/DNS provider: infrastructure and recovery boundaries; account access is not implied by GitHub access.
- Optional later systems: Instagram account maintenance, Reddit and an external CRM are not first-version commitments. Integration extensibility is accepted; selection of those integrations remains separate.
- Server-side AI/model API calls are excluded by owner decision. A client-facing MCP/service interface is not a model-provider API and remains in scope.

The VPS receives and stores events while a ChatGPT conversation is closed. That does not itself start a ChatGPT conversation or guarantee that the assistant is continuously running. Notifications and any unattended processing require an explicit product decision.

### Integration extensibility — accepted product requirement

New external services must be introducible through separately developed integration modules or adapters, preserving the product's owner authority, approval history, enquiry context and observable action outcomes.
The initial concrete integrations remain company Facebook publishing, Meta advertising and WhatsApp Business. They provide the first real cases against which the extension boundary will later be designed.

Each integration has an explicit supported capability scope, external account scope and credential needs. Differences between platforms remain visible: support for publishing does not imply advertising, inbox access, attachments or every action of another platform.
The product must be able to state that an operation is unavailable, an account lacks permission, or an integration is disconnected. An extension must not invent data or replace an unsupported action with a different external action.

An owner must be able to stop an integration's external actions and see its connection state. What remains readable, how inbound events are treated, and how pending or uncertain actions are handled after disablement must be decided explicitly in States 1–2.

This requirement is not permission to download or execute arbitrary integration code from a customer message or assistant response. Automatic discovery, installation, hot-loading, a public adapter marketplace and arbitrary user-supplied code are not first-version promises.
How approved integration code is added, versioned, tested and deployed is a later architecture/release decision.

The common behaviour that integrations must preserve and their exact contracts are not designed here. Models and rules come before responsibility boundaries and public APIs; no generic operation/payload abstraction is accepted merely to make an adapter appear universal.

## 7. State 0 trust boundaries

### Owner and assistant authority

Only the owner may connect integrations, approve updates or change access permissions. The ChatGPT and local-agent clients cannot expand their own authority.
Only an authenticated owner may authorize the product's external changes.
Assistant proposals and customer messages are not grants of authority.
Permission to deploy code, read conversations, send a reply and change advertising are separate authorities.
The mechanism and lifecycle of approval are not yet designed.
Decisions discussed in chat must be distinguishable from machine proposals when used by the service. The local agent cannot turn its own proposal, a quoted chat message or another client's assertion into owner approval.
A shared service record of decisions and action outcomes must serve both clients; two machine clients must not keep conflicting private approval histories. The identity, consistency and concurrency rules belong to States 1–2.

### ChatGPT, plugin and public network

The remote tool interface crosses a public-network and authentication boundary.
An unlisted URL is not an authentication decision.
The service exposes bounded business operations, not a general shell, arbitrary file access, arbitrary outbound requests or unrestricted access to the whole VPS.
Exact authentication and allowed public surfaces remain to be selected.

### Local-agent access and phone emergency control

ChatGPT and the local agent require separate authenticatable, independently revocable client identities. Exact authentication and permission grants remain open; sharing one unrestricted administrative credential is not an accepted design.
Service-client access is distinct from developer SSH/deployment access. One does not grant the other.
The same owner authority and external-action boundaries apply to both machine clients. Concurrent or repeated requests from either client must not create duplicate effects; exact rules belong to States 1–2.

The owner selected an emergency red button on the phone that freezes outbound effectful actions from both machine clients while preserving the website and receipt of enquiries.
The freeze applies across integrations to actions such as sending customer messages, publishing content and creating or changing advertising, including previously requested work that has not yet been submitted externally. It is enforced by the service; client cooperation is not the control boundary.
Read-only platform queries and necessary acknowledgements of inbound events are not effectful business actions. This is not a network-egress shutdown. There is no automatic customer-facing reply exception to the chosen freeze.

The control must distinguish a recorded freeze from a failed or unreachable control. Requests already accepted by an external platform cannot be recalled by this freeze, and already-running Meta advertising continues independently. Pausing that advertising would be a separate explicitly authorized action.

The following recovery and availability considerations remain proposals or open decisions:
- the owner can reach the phone control without needing either machine client to cooperate;
- later recovery exposes uncertain/in-flight actions before resuming, rather than silently replaying them;
- who may resume, whether a restart preserves the stopped state, and the independent recovery route when the VPS is unreachable must be decided in States 1–2.

VPS shutdown and stopping the inbound marketing process are not the selected red-button behaviour.

The current project draft does not authorize exposing host-shutdown commands to either machine client or changing the live host.

### Meta connections and inbound events

Meta credentials and asset grants determine which external operations are available.
Webhook verification, event authenticity, duplicate delivery and external retries require explicit treatment in States 1–2.
Knowing an account ID or a customer's phone number does not authorize access or sending.
Integration installation, credential access, owner authorization and external account permissions are separate boundaries. Adding an integration does not inherit another integration's credentials or external-action authority.

### Customer content and files

Messages, linked pages and uploaded media remain untrusted material even when received through an authentic integration.
They cannot authorize a change to advertising, disclose another customer's conversation, grant access or execute instructions on the host.
Photographs are in first-version scope; exact accepted image forms, processing limits, protected access and isolation remain unresolved. Voice processing is excluded from the first version.

### Secrets

Meta tokens, app secrets, plugin credentials, deployment keys and backup keys are sensitive.
They are not returned to the assistant as business results, committed to GitHub, or included in ordinary logs.
Credential issue, rotation, expiration and revocation need their own lifecycle decisions.
No real credential is needed to author this specification.

### Existing VPS and website

The site, the new service, database, deployment authority and host administration are distinct trust areas even if they share one machine.
A separate process or container does not provide a separate-host boundary.
Access to the website's files, other hosted applications, nginx administration or a container daemon is not an implicit product capability.
Actual network exposure and host security remain unverified.

### Customer data and AI processing

Customer messages and contact details are private working data.
Using ChatGPT to discuss them crosses an external processing boundary; the minimum necessary context, access and retention must be defined before live use.
The VPS does not call model-provider APIs or run unattended AI translation/drafting. Translation and drafting take place in the ChatGPT or local-agent client; the server stores only the agreed working records and executes authorized integration actions. Automatic voice transcription is excluded from the first version.
No separate first-version customer dashboard is required; the owner works in ChatGPT and on the phone. The small emergency-stop surface is still needed and does not imply a broader administrative UI.

### Releases, backups and logs

Reviewed source, deployed release, operational credentials, database and backup storage have different access needs.
Backups require a restore test; a backup existing on the same VPS is not a complete recovery plan.
Logs must support diagnosis without becoming an uncontrolled copy of conversations and credentials.

## 8. Constraints and first-version exclusions

- Do not buy subscriptions, enter payment details, transfer the working WhatsApp number or change existing connections as an incidental setup step.
- Do not change live advertising or contact real customers while testing without explicit authorization for that action.
- Do not require Supermetrics or Windsor.ai as the product's permanent execution layer.
- Do not promise that Meta API exposes every action available in Ads Manager.
- Do not promise coexistence with the phone application until the owner's actual onboarding route is verified.
- Server-side model-provider API calls and AI gateways are excluded; no AI API key or separate server-side inference budget is required by this design. Client subscriptions or local-agent access are outside the service's model-calling responsibility.
- Automatic voice transcription, translation and audio archiving are outside the first version; the owner listens on the phone.
- Unattended spending decisions, automatic sales negotiation and bulk outreach are outside the proposed first version.
- Reddit, full accounting, invoicing, payments, contract generation, a public CRM product and multi-tenant operation are deferred.
- Python is selected for the VPS service and integration adapters. This State 0 does not select module boundaries, contracts, algorithms, Python version, framework or dependencies.

## 9. Open questions

1. Product acceptance: does the owner accept the proposed first-version boundaries, including reviewed sending and separate advertising activation?
2. First-release channel scope: which company Facebook Page actions (posts, comments, inbox) and assets are required? Instagram maintenance is a possible later integration unless separately selected; extensibility does not settle this scope.
3. Meta access: does a suitable developer app exist, which permissions are available, and which company assets can it use?
4. WhatsApp onboarding: is official phone/API coexistence available for this business and number, directly or through a provider? What remains usable on the phone?
5. Customer photographs: which image forms and sizes are supported, how are originals accessed, and what retention applies? Text/photos versus voice scope is settled: photographs are included; voice messages stay on the phone without automatic transcription.
6. Minimal storage and privacy: which durable action/control records and working message/photo context are required, which customer facts may be sent to ChatGPT, what notice is needed, and what retention/deletion/backup rules apply? The owner prefers simplicity and has not approved a full permanent conversation archive.
7. Infrastructure: actual VPS provider, OS, capacity, existing workloads, listeners, firewall, recovery route, updates, TLS renewal and verified backup coverage?
8. Client and owner access: separate authentication and revocation for ChatGPT and the local agent; exact permission scopes; how owner decisions discussed in chat become service-verifiable authority; authentication for the phone control? The owner has chosen ChatGPT plus the phone without a separate enquiry dashboard and reserved integration, update and permission administration to the owner.
9. Operational continuity and emergency recovery: WhatsApp is the selected notification channel; determine the authorized recipient, supported delivery path and behaviour during outages. Distinguish the existing phone application's notifications from notifications sent by the new service. A failed VPS cannot guarantee its own WhatsApp alert, and notifications must not silently bypass the outbound freeze. How is the phone control reached independently of both clients? The stop scope is settled: block outbound effects from both clients, preserve the website and inbound enquiries. Who can resume, does a restart preserve the freeze, and how is unsent or uncertain work reviewed before resumption? An emergency Meta-advertising pause, if wanted, is a separate action.
10. Advertising authority: allowed assets, budget limits and which later actions may run without a new owner decision?
11. Development and deployment: implementation repository, deployment actor, release approval and rollback policy?
12. Enquiry attribution: what evidence connects a WhatsApp enquiry to a particular advertisement, and how are unknown sources represented without guessing?
13. Costs: explain the possible recurring costs of infrastructure, backup/monitoring, and Meta API messaging or an onboarding provider. Server-side AI API costs are excluded because the server makes no model-provider calls. Obtain an estimate from actual usage and the chosen route before asking the owner for a spending ceiling. Advertising budget is separate. No paid service, new subscription or spending budget is approved.
14. Recovery semantics: how are uncertain external submissions resolved without double-sending or duplicate creation?
15. Integration lifecycle: the owner alone approves updates, connections and permission changes. Define compatibility/capability checks, the permitted deployment actor, and what happens to inbound events, readable data and pending actions when an integration is disabled or upgraded.

These are recorded gaps, not implementation defaults. State 1 and later states must not silently decide them.

## 10. State 0 question checklist

- Goal, actors, primary actions, inputs, outputs, persistent facts, integrations, constraints and unknowns are recorded in sections 1–9.
- Section 4 names an owner action, an observable result and a failure/uncertainty outcome for each current product promise.
- Unverified access, onboarding, topology, photograph handling details, privacy, unattended behaviour and costs are explicitly listed as open questions. The owner has selected text/photos and excluded automatic voice processing.

## 11. Handoff and verification status

This is the State 0 draft updated with the owner's media-scope, Python, integration-extensibility and two-client decisions. The owner selected the phone emergency-stop scope: outbound effects frozen, website and inbound enquiries preserved. Authentication and recovery semantics remain open. It is not a completed application, an accepted security review, an approved deployment plan or evidence of a working direct Meta integration.
No State 1 source, assembled global_spec.json or Factory export is created.

Authoring CLI and State 0 question rounds have not been run in this session. Two clean reviews of the current State 0 text have not been obtained.
The index-registration PR #127 ran repository CI: 1211 tests passed, ownership and durable-archive reviews passed; the aggregate job failed on cabinet-web-backend projection verification, also reproduced on its base main. This does not constitute semantic acceptance of this State 0.
Continue through the common Workbench pipeline after project registration; do not skip to code or exact contracts.

Infrastructure reference:
https://github.com/MigelSmirnov/Vital-Vibe-Constructions/blob/main/architecture/vps-cutover-20260913/report.md
