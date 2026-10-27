# Cabinet Kernel — requests from the Registry case, 2026-10-27

For the session that next opens this case. The Registry case (spec-workbench
`agent/registry`, `examples/registry/00_product.md`, State 0 closed at
`82b36b1a`) places one requirement on Cabinet Kernel and raises three
questions about K-14. None of them is a decision of this case yet: each is
taken up here, by this case's own rounds and the owner.

## 1. Requirement: Kernel names the agent session from its run context (Registry R0-77)

Registry gives each agent session its own set of projects (R0-46). On every
agent-authority call it checks that Kernel authenticated with its token, that
the session the call names is registered, and that the `project_id` is in that
session's set (R0-53). Sessions carry no secret: Registry trusts Kernel to name
the session it acts for. Kernel registers sessions with Registry (R0-47).

The session a call names must be set by Kernel from the context of its own run,
never by a value the agent's flow supplies. A flow that could set it could name
another session and reach that session's projects.

Today Kernel cannot meet this:

- This case has no notion of an agent session. K-15 has agent tokens configured
  in the installation; nothing ties a run to a session Registry knows.
- A08 rule 4: "the kernel adds no header or field of its own". Every value sent
  to a service is an input port of the binding, so a session id could only come
  from the flow.

Until this is met, Registry binds none of its agent-authority operations in
Kernel (R0-77). What this case has to decide:

- what an agent session is for Kernel — one per agent token (K-15), one per
  conversation, or something the owner opens — and how a run knows its session;
- how Kernel registers a session with Registry and when;
- how the session reaches the request: a header or field Kernel sets itself, as
  a narrowing of A08 rule 4, and how the manifest record declares it so that no
  input port can carry it (Registry R0-78 leaves the format to the platform).

## 2. Questions about K-14 (personal data never reaches an agent)

Registry closed its side: Kernel's Registry token never allows `personal_data`,
as a boundary the owner cannot widen (Registry R0-74). Other services whose
tokens do allow it — Cabinet, PresuPro, Client Portal — may still pass such
values to Kernel under their own contracts (Registry R0-76), and Registry's
guarantee stops at what Registry itself gives Kernel. So K-14 is the
platform's end-to-end guarantee, and three points of it are open:

1. **Outcomes as a side channel.** Code the agent writes runs in Kernel. A
   function whose execution received a `personal_data` value can turn it into
   an observable effect: a run's status, failure, verdict, time or resource
   use, one bit per run. K-14 classes the function's output, not these. Should
   an agent-authored function receive `personal_data` at all, or should the
   observable outcome of a run that received one reach the owner only?
2. **Digests of low-entropy values.** Where a value would reach an agent, K-14
   returns its digest and class. A plain SHA-256 of a phone number, a tax id
   (NIF/NIE/CIF) or a street address is reversed by enumerating candidates.
   Should the digest be keyed (an HMAC with an installation secret the agent
   never sees), or should such values reach an agent as class only?
3. **Values that arrive from other services.** K-14 is the only rule that stops
   a `personal_data` value that Cabinet, PresuPro or Client Portal pass to
   Kernel from reaching the agent. The bindings of those services must declare
   the class of each output faithfully; who checks that a service declares
   `personal_data` where it returns one?

## Registry decisions cited

R0-46, R0-47, R0-53 (sessions and their checks), R0-74 (Kernel's token never
allows `personal_data`), R0-76 (Cabinet's token does), R0-77 (this
requirement), R0-78 (the manifest record). Read them in
`examples/registry/00_product.md` on `agent/registry`.
