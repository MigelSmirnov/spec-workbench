# State 1, round 1 (emulated)

Reviewed `01_models.md` and `00_product.md` at commit `ac22977`. Reviews: 17, 20, 20
points. Topics raised by two or more reviews: 15; by one: 4. All judge quotes
verified verbatim against the reviewed texts.

| topic | reviews | kind | closed by |
|---|---|---|---|
| T01 Project last-changed instant: stored fact or derived / written once | 3 | **contradiction** | M01: the last-changed instant is a stored fact that moves as 'Revisions and times' says; 'written once' and 'd |
| T02 Which actions move the Project and Customer revision | 3 | **consequential_gap** | Revisions and times: the revision moves exactly when the last-changed instant moves, and the two are one fact  |
| T03 Instants and revisions of imported records | 3 | **consequential_gap** | Revisions and times: the import keeps the source's created, last-changed, archived and published instants; rev |
| T04 Identity format: UUID settled vs owner's choice with a v1 mapping | 3 | **contradiction** | Identity formats: the format is a UUID, settled; the import keeps ids verbatim; the mapping sentence struck. |
| T05 What an erased Customer keeps (kind, marks, revision) | 3 | **contradiction** | M04 follows State 0: an erased Customer keeps `customer_ref`, the erased mark and its instant; kind, revision, |
| T06 Does the contact-data erasure erase fiscal data | 2 | answered | M04 cites R0-06 for the fiscal values going with the erasure (no text change needed beyond T05). |
| T07 Erasure and the restricted/ended marks: settled or State 2 | 3 | **contradiction** | M04: erasure clears the restricted and ended marks (nothing but identity and the erased fact survives); restri |
| T08 The Customer the import makes: kind, name, non-tax values, one per v1 value | 3 | **consequential_gap** | M04: no v1 `customer_ref` was minted by Registry (L03: an opaque caller string), so the import makes one new C |
| T09 What an anonymised project keeps (instants) vs R0-62 | 3 | **contradiction** | M01 follows State 0: an anonymised project keeps `project_id`, status `archived`, the anonymised mark and its  |
| T10 Object kind (and Customer language): vocabulary or free text; required? | 3 | **consequential_gap** | M02 and Declared vocabularies: the object's kind is a closed vocabulary the specification declares, optional a |
| T11 Room's acting principal: a new fact State 0 does not name | 2 | **consequential_gap** | M03: the acting principal is struck from the Room; a room carries its id, name, project and the instant it was |
| T12 Confirmation id: who mints it, is there a model | 3 | **consequential_gap** | M11 and Identity formats: Registry mints the confirmation id when the owner confirms an action that asks for c |
| T13 Which actions write an audit entry | 3 | **consequential_gap** | M09 lists the actions that write an entry: create, correct, archive, anonymise and delete a project; record, c |
| T14 Access version: settled in facts, deferred in Open questions | 3 | **contradiction** | M06: what moves the version is State 1's — every change of the granted set, the active project or the pending  |
| T15 Disclosure classes: context-dependent marks and unclassed facts | 2 | **contradiction** | Disclosure classes: each fact has one class; the ended date and the restriction mark are `business_confidentia |

Not clear: 14 blocking topics, all closed in `01_models.md` in the next commit.
Two closures follow State 0's text over the owner's answers of 2026-10-31:
T05 (an erased Customer keeps only `customer_ref` and the erased mark — not its
kind, R0-06) and T09 (an anonymised project keeps no instant, R0-62). Keeping
either would be a new State 0 decision. Single topics S1–S4 are not judged.
Next: round 2 on the edited units.
