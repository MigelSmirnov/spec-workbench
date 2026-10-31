You are a second author taking over an open State 2 question of the Registry
design case (a spec-workbench project). The previous author left a packet:
the question, the accepted bases, the State 2 rules that bear on it, the
admissible histories found so far, and a proposed edit. The packet is the file

  experiments/registry-state2-authoring/packet/BUNDLE.md

in the repository at /home/user/spec-workbench. Read it first.

Your tasks:

1. Reconstruct the grounds: which accepted passages (State 0, State 1, State 2)
   any answer to the question must respect, and why.
2. Check the proposed edit: does it keep every accepted passage and every
   history marked "accepted"? Does it follow from the texts, or is it one
   choice among several the texts allow? If several, name them and what
   separates them, and say who has to choose (the State 2 author or the owner)
   and why.
3. Find neighbours the edit touches — rules, decisions, histories, later
   states — and try to build a counterexample: an admissible history where
   the edited text gives a wrong, ambiguous or contradictory answer.
4. Where you lack context, do not guess.

Context rules:

- You MAY read the Registry design texts at the canonical commit, e.g.
  `git -C /home/user/spec-workbench show cf675e5c:examples/registry/02_rules_records.md`
  (also 00_product.md, 01_models.md, the other 02_rules_*.md, and
  examples/registry/questions/). Log EVERY such read in "source_accesses":
  what you read and why the packet was not enough.
- Do NOT read anything under experiments/ other than packet/BUNDLE.md, nor
  other branches. The previous author's conclusions are deliberately not
  given to you.
- If you need something you cannot or may not read, put a precise request in
  "requests" (what, and what you would decide with it). You may stop there;
  the requests will be answered and you will be asked to continue.

Answer with one JSON object only:
{"grounds":[{"passage":"<key or file:rule>","why":"..."}],
 "patch_check":{"keeps_accepted":"yes|no|unsure","detail":"...","follows_from_texts":"yes|no — one of several","alternatives":[{"name":"...","behaviour":"...","grounds":"..."}],"who_chooses":"author|owner","why_who":"..."},
 "neighbours":[{"what":"...","effect_of_edit":"..."}],
 "counterexamples":[{"history":"...","problem":"...","admissible":"yes|no|unsure"}],
 "requests":[{"need":"...","to_decide":"..."}],
 "source_accesses":[{"read":"...","why":"..."}]}
