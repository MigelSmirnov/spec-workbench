"""The two instructions of a round: ask, then group what was asked."""
from __future__ import annotations

ASK = """You review a design BEFORE the next states, modules and code exist.
You receive the accepted design texts up to State {state}. Later, other agents will
write the next states and the code from these texts alone; whatever the texts leave
open, they will decide silently, and different agents will decide differently.

List every point where continuing from these texts would force a guess.

Scope of State {state} — report a point only if it belongs here:
{scope}

Two texts that contradict each other always belong here. Points the texts list on
purpose as carried to a later state do not.

Do not propose designs as settled. Report only genuine gaps, not style.
Output strict JSON, nothing else:
{{"open_points":[{{"subject":"<model, decision, action or section>","kind":"<short kind>","text":"<the exact phrase that is silent, vague or contradictory>","question":"<the question the texts must answer>","options":["<option you see>"],"default_guess":"<what you would do if forced>"}}]}}"""

GROUP = """You receive the open points of several independent reviews of the same
design texts. Group the points that ask about the same missing decision, even
when worded differently. A point belongs to exactly one group; a point unlike any
other is a group of its own.

Output strict JSON, nothing else:
{"groups":[{"topic":"<one line naming the missing decision>","members":["<point id>"]}]}"""


def ask_instruction(state: int, scope: str) -> str:
    return ASK.format(state=state, scope=scope)


def ask_input(documents: list[tuple[int, str, str]]) -> str:
    return "\n\n".join(f"=== {name} (State {state}) ===\n\n{text}" for state, name, text in documents)
