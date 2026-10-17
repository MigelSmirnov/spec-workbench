# State 0 — VVC Marketing Workspace (simplified)

Status: draft for owner review; not accepted or closed.
Created: 2026-10-17. Supersedes the 2026-10-17 draft after the owner chose to simplify scope.
Project: `vvc-marketing-workspace`. Canonical ref: `agent/vvc-marketing-workspace`.
Owner: Vital Vibe Construction.

## 1. Product goal

The owner discusses a post, an article adaptation or an advertising idea with ChatGPT and the assistant then executes it: publishes on the company Facebook Page and creates, enables, pauses or adjusts Meta advertising. The assistant is the owner's hands for Facebook and Meta ads; the owner stays the one who decides.

A reported external result is the only proof of completion. A tool acknowledgement or an optimistic answer is not a published post or a running campaign.

## 2. Decisions (owner, 2026-10-17)

- Scope of the first version: company Facebook Page publishing and Meta advertising. Nothing else.
- WhatsApp is out of scope. Customer enquiries stay in the WhatsApp Business app on the phone; the owner forwards a message or photo into ChatGPT by hand when a Spanish/Russian discussion is needed. No WhatsApp API, number migration, webhook, enquiry storage or notification service.
- Page comments and Page private messages are out of the first version. They may be added later as an owner decision.
- One machine client: ChatGPT, connected to a small service on the owner's VPS (ChatGPT connector / Actions or MCP — exact mechanism to be verified in the owner's account). A local coding agent (Codex) is a developer tool, not a client of the service.
- The owner's instruction in the chat is the command. When the owner tells the assistant to publish, enable, pause or change a budget, the assistant calls the service and the service records what was asked, what it sent to Meta and what Meta answered. The service does not try to prove the owner's intent beyond the authenticated connector call; the owner accepts this for the chosen scope.
- Advertising prepared by the assistant is created paused. Enabling it and changing budgets are allowed from the chat only within an owner-set spending ceiling (amount to be chosen in State 2). Outside that ceiling the owner acts in Meta Business Suite by hand.
- Kill switch: one owner-only control that makes the service refuse every effectful call (publish, enable, budget change, create). Reads keep working. Simplest acceptable form is a single toggle; revoking the connector is the fallback. It does not stop advertising that is already running.
- The server does not call AI/model APIs. Drafting and translation happen in ChatGPT; the server only executes Meta actions and keeps the action log.
- Storage is minimal: the action log (request, Meta response, external IDs, timestamps), the kill-switch state and credential references. Drafts live in the chat. SQLite or a file store is acceptable; chosen in State 1.
- Extensible core (owner requirement): the service is a small core plus integration adapters. The core owns what every integration shares — connector authentication, the action log, the kill switch, the spending ceiling, credential references and outcome reporting. Each external platform is a separately developed adapter with its own declared capabilities and credentials. Facebook Page publishing and Meta Ads are the first two adapters; WhatsApp, Instagram, Page comments or others can be added later without changing the core. An adapter must say when an operation is unsupported rather than substitute another one, and adding an adapter does not inherit another adapter's credentials or authority. Adapters are added only through reviewed, owner-approved releases: no hot-loading, no marketplace, no code taken from a chat. The adapter contract itself is designed in State 3 against the two real cases, not abstracted upfront.
- Python for the service. Version, framework and deployment are chosen later.
- The owner alone connects Meta assets, rotates credentials and approves releases.

## 3. Actors

- Owner: decides content, destination, budget and timing; operates the kill switch; owns Meta assets and credentials.
- Assistant in ChatGPT: drafts, explains, proposes and executes through the service on the owner's instruction.
- VPS service: core plus adapters. The core authenticates the connector, records and reports outcomes, enforces the kill switch and the spending ceiling; adapters execute bounded operations on one external platform each (first: Facebook Page, Meta Ads).
- Meta: authoritative source of publication and advertising state.
- Developer/deployer (owner, possibly using Codex): changes and deploys the service. Deployment access is not connector access.

## 4. Product actions

| Owner action in chat | Observable result | Failure or uncertainty |
| --- | --- | --- |
| Adapt a website article / write a post | Editable draft in the chat, source link preserved | Missing facts or media are asked, not invented |
| "Publish" | Post ID and verified status on the Page | Rejection shown; uncertain submission reported as uncertain, not retried blindly |
| Prepare advertising (goal, audience, creative, budget) | Paused campaign/ad set/ad with IDs and a comparison against what was requested | Partial creation and changed defaults listed individually |
| "Enable" / "pause" / "set budget to X" | Verified status or budget as Meta reports it | Refused when above the ceiling or when the kill switch is on; ambiguous outcome surfaced |
| "How is the campaign doing?" | Spend, results and status read from Meta | Unavailable metrics stated as unavailable |
| Kill switch | Service refuses effectful calls and shows the stopped state | An unreachable control is not reported as stopped |

Not promised: every Ads Manager feature (the API covers less), comment handling, inbox handling, WhatsApp, unattended posting or spending.

## 5. External systems and boundaries

- ChatGPT connector: public-network, authenticated boundary; the service exposes only the operations in §4, no shell or file access.
- Meta Graph/Marketing API: Page publishing (`pages_manage_posts` or equivalent) and ads (`ads_management`) on explicitly connected assets. A suitable Meta developer app and its permission level are unverified; the owner currently cannot log into Meta for Developers.
- Company website (`MigelSmirnov/Vital-Vibe-Constructions`): source of articles. The service reads published articles; it gets no deployment or file access.
- Existing VPS: the service is a neighbour of the website; host hardening and network exposure are unverified (see the September cutover report).
- Secrets (Meta tokens, connector credential) never appear in chat answers, logs or GitHub.

## 6. Open questions for State 0 closure

1. Meta access: which developer app, which permission level, which Page and ad account? Does the owner need to recover Meta for Developers login first?
2. Spending ceiling: what monthly amount may the chat enable/adjust without the owner touching Business Suite?
3. Connector mechanism actually available in the owner's ChatGPT account.
4. Kill switch form: small web toggle on the VPS, or revoke-the-connector only?
5. Deployment: who deploys releases and from which repository?
6. VPS audit before deployment (resources, listeners, firewall, backups, TLS renewal).
7. Recurring costs: VPS already paid; Meta API is free for Page/ads use; remaining cost is the owner's ChatGPT plan. Confirm no new subscription is needed.

Deferred, not open: WhatsApp API, comments, Page inbox, Instagram, Reddit, CRM, server-side AI. Each of these is a candidate adapter, not a change to the core.

## 7. Handoff

State 0 is closed when §2 decisions are confirmed and questions 1–4 are answered. Then State 1 (models: action log, campaign references, kill-switch state, adapter/capability registry), State 2 (rules: ceiling, kill switch, idempotency of retries) and State 3 (core vs adapter responsibilities, derived from the two real adapters).
