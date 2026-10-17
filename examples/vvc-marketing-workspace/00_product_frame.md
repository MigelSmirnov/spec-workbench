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
- A personal plugin connecting ChatGPT to the owner's service is the intended interaction surface.
- Reddit is a possible later direction; the owner deferred its format and priority.
- Login to Meta for Developers is currently unavailable to the owner. Whether a suitable Meta app exists is unknown.
- The owner explicitly requested consideration of VPS requirements and security before implementation.
- Integration extensibility is required: the architecture must allow separately developed integration modules or adapters (owner decision, 2026-10-17). This decision does not by itself include Instagram or Reddit in the first release.

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
- Assistant in ChatGPT: explains retrieved data and proposes content or actions; it is not the source of authority for spending, sending or changing permissions.
- Customer: sends text and potentially media through WhatsApp. Customer content is untrusted input, not an administrative instruction.
- VPS service: receives integration events, retains the agreed working records, exposes authorized product actions and reports external outcomes.
- Meta services: authoritative source of actual advertising, publication and WhatsApp-message outcomes within granted permissions.
- Developer/deployer: changes reviewed code and deploys releases; development access is distinct from authority to send a message or launch advertising.

## 4. Product actions and observable outcomes

| Owner action | Inputs | Observable result | Failure or uncertainty |
| --- | --- | --- | --- |
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
| Revoke integration access | Owner's revocation decision | Product stops using the revoked authority and reports its state | External revocation that cannot be verified is reported as unresolved |

Publication, advertising and WhatsApp operations are conditional on each external system granting the necessary access. This table is a product promise inventory, not an API contract or implementation algorithm.

## 5. Inputs, outputs and persistent facts

Inputs include the owner's instructions, authorized asset selections, business descriptions, approved photographs and texts, platform observations, and customer messages.
First-version attachments are customer photographs, associated with their source messages and conversation. Supported image formats, size limits, retention and protected access remain to be designed.
Voice messages remain handled by the owner in the phone application. The first version does not promise voice transcription, translation or audio archiving; the owner may supply a text summary for discussion.

Outputs include retrieved observations, bilingual drafts, approval previews, externally created object identities, observed external statuses, enquiry status histories and operator-visible failures.

Persistent facts needed by the product:
- owner and connection identity, allowed asset scope and access status;
- original conversation events, participants and external message identities;
- received photographs and their association with the source conversation and message, subject to the retention decision;
- enquiry assessments and owner-entered business facts;
- drafts and the exact version considered by the owner;
- approval/refusal decisions and the external action they concern;
- action attempts, partial outcomes, external evidence and unresolved submissions;
- credential references and lifecycle records, separate from ordinary business data;
- release identity and operational recovery records.

Exact models, identifiers, status vocabularies, schema fields and retention durations belong to later design work or the open questions below.

## 6. External systems and product boundaries

- ChatGPT personal plugin / remote MCP: authorized owner-facing product operations; availability in the owner's account remains to be tested.
- Meta Marketing API: advertisement operations on explicitly authorized company assets.
- Facebook publication APIs: required page identity and permissions remain to be verified separately from advertising permissions.
- WhatsApp Business Platform: message delivery and inbound events; working-number onboarding and phone/API coexistence remain unresolved.
- Existing website: neighbouring production workload, not part of the marketing service's writable data.
- GitHub: source and review history. This specification repository is public; actual customer data, credentials and private operational evidence are not project files.
- VPS provider and domain/DNS provider: infrastructure and recovery boundaries; account access is not implied by GitHub access.
- Optional later systems: Instagram account maintenance, Reddit, an external CRM and server-side AI inference are not first-version commitments. Integration extensibility is accepted; selection of those integrations remains separate.

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

Only an authenticated owner may authorize the product's external changes.
Assistant proposals and customer messages are not grants of authority.
Permission to deploy code, read conversations, send a reply and change advertising are separate authorities.
The mechanism and lifecycle of approval are not yet designed.

### ChatGPT, plugin and public network

The remote tool interface crosses a public-network and authentication boundary.
An unlisted URL is not an authentication decision.
The service exposes bounded business operations, not a general shell, arbitrary file access, arbitrary outbound requests or unrestricted access to the whole VPS.
Exact authentication and allowed public surfaces remain to be selected.

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
Whether text translation runs unattended on the VPS is undecided. Automatic voice transcription is excluded from the first version.

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
- Automatic voice transcription, translation and audio archiving are outside the first version; the owner listens on the phone.
- Unattended spending decisions, automatic sales negotiation and bulk outreach are outside the proposed first version.
- Reddit, full accounting, invoicing, payments, contract generation, a public CRM product and multi-tenant operation are deferred.
- This State 0 does not select modules, contracts, algorithms or a final software stack.

## 9. Open questions

1. Product acceptance: does the owner accept the proposed first-version boundaries, including reviewed sending and separate advertising activation?
2. First-release channel scope: which company Facebook Page actions (posts, comments, inbox) and assets are required? Instagram maintenance is a possible later integration unless separately selected; extensibility does not settle this scope.
3. Meta access: does a suitable developer app exist, which permissions are available, and which company assets can it use?
4. WhatsApp onboarding: is official phone/API coexistence available for this business and number, directly or through a provider? What remains usable on the phone?
5. Customer photographs: which image forms and sizes are supported, how are originals accessed, and what retention applies? Text/photos versus voice scope is settled: photographs are included; voice messages stay on the phone without automatic transcription.
6. Privacy: which customer facts may be sent to ChatGPT, what notice is needed, how long are messages and attachments retained, and how are deletion requests handled?
7. Infrastructure: actual VPS provider, OS, capacity, existing workloads, listeners, firewall, recovery route, updates, TLS renewal and verified backup coverage?
8. Owner access: authentication for the plugin, session revocation, and any owner-facing interface outside ChatGPT?
9. Operational continuity: how does the owner learn about a new enquiry, and what response remains possible while ChatGPT, the plugin or the VPS is unavailable?
10. Advertising authority: allowed assets, budget limits and which later actions may run without a new owner decision?
11. Development and deployment: implementation repository, deployment actor, release approval and rollback policy?
12. Enquiry attribution: what evidence connects a WhatsApp enquiry to a particular advertisement, and how are unknown sources represented without guessing?
13. Costs: acceptable infrastructure, Meta messaging and optional AI-processing costs? No paid service is selected.
14. Recovery semantics: how are uncertain external submissions resolved without double-sending or duplicate creation?
15. Integration lifecycle: who may approve integration releases, what compatibility and capability checks are required, and what happens to inbound events, readable data and pending actions when an integration is disabled or upgraded?

These are recorded gaps, not implementation defaults. State 1 and later states must not silently decide them.

## 10. State 0 question checklist

- Goal, actors, primary actions, inputs, outputs, persistent facts, integrations, constraints and unknowns are recorded in sections 1–9.
- Section 4 names an owner action, an observable result and a failure/uncertainty outcome for each current product promise.
- Unverified access, onboarding, topology, photograph handling details, privacy, unattended behaviour and costs are explicitly listed as open questions. The owner has selected text/photos and excluded automatic voice processing.

## 11. Handoff and verification status

This is the State 0 draft updated with the owner's media-scope and integration-extensibility decisions. It is not a completed application, an accepted security review, an approved deployment plan or evidence of a working direct Meta integration.
No State 1 source, assembled global_spec.json or Factory export is created.

Authoring CLI and State 0 question rounds have not been run in this session. Two clean reviews of the current State 0 text have not been obtained.
The index-registration PR #127 ran repository CI: 1211 tests passed, ownership and durable-archive reviews passed; the aggregate job failed on cabinet-web-backend projection verification, also reproduced on its base main. This does not constitute semantic acceptance of this State 0.
Continue through the common Workbench pipeline after project registration; do not skip to code or exact contracts.

Infrastructure reference:
https://github.com/MigelSmirnov/Vital-Vibe-Constructions/blob/main/architecture/vps-cutover-20260913/report.md
