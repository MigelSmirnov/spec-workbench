#
# The adapter. It turns the Kernel's input ports into calls of the model above
# and the model's answer into two output ports. It adds no rule.
#
# Input ports (value carriage, JSON):
#   version         one of VERSIONS' names: V0 .. V6, H1
#   interpretation  {reading: value}; missing readings take the model's defaults
#   initial         {"setup_events": [event, ...]}: the initial state, given as
#                   the admissible history that reaches it from an empty store
#   events          [event, ...]: the events under study
#   mode            {"kind": "trace"} or
#                   {"kind": "explore", "depth": n, "with_restore": bool}
# Event: {"kind": ..., "name"?, "stale"?, "conf_ok"?, "date_rel"?, "fail"?}
#
# Output ports:
#   observation     what the owner would see: each studied step's answer, the
#                   project card and the log at the end
#   analysis        the model's own findings: per step the verdict
#                   (determined / conflict / ambiguity / out_of_store / no_audit),
#                   conflict sets and their resolution, the outcomes left open;
#                   for "explore", the findings of the bounded search
#
# A conflict or an ambiguity is a *result*: the function succeeds and reports
# it. Only a malformed input is an error of the function (it raises, and the
# Kernel records the execution as crashed).

ENTRY_DEFAULT_READINGS = {
    "own_entry_is_change": False,
    "a15_inv_presupposes": True,
    "a14_inv_reading": "at_commit",
    "durable_counter": "in_store",
    "v0_counter": "kept",
    "a05_covers_empty_erasure": False,
    "id_formats_strict": False,
}
_EVENT_FIELDS = {"kind", "name", "stale", "conf_ok", "date_rel", "fail"}


class InputError(ValueError):
    pass


def _event(d):
    if not isinstance(d, dict) or not set(d) <= _EVENT_FIELDS or "kind" not in d:
        raise InputError(f"malformed event: {d!r}")
    return Event(**d)


def _outcome_label(o):
    return o.label()


def _step_record(s):
    rec = {"event": s.event.label(), "verdict": s.verdict,
           "answer": [s.checked.answer, list(s.checked.reasons)]}
    if s.verdict == "conflict":
        rec["conflict_sets"] = [list(c) for c in s.conflict_sets]
        rec["resolution"] = s.resolution
    if s.verdict in ("ambiguity", "out_of_store"):
        rec["outcomes"] = sorted(_outcome_label(o) for o, _ in s.passing)
    return rec


def _trace(version, interp, setup, events):
    rules = rules_for(version)
    w = initial()
    for ev in setup:                       # reach the initial state
        s = step(w, ev, rules, version, interp)
        if s.verdict in ("conflict", "out_of_store") or not s.passing:
            return None, {"setup_failed_at": ev.label(), "verdict": s.verdict}, []
        w = s.passing[0][1]
    recs = []
    for ev in events:
        s = step(w, ev, rules, version, interp)
        recs.append(s)
        if s.verdict in ("conflict", "out_of_store"):
            break
        w = s.passing[0][1]
    return w, None, recs


def _explore(version, interp, depth, with_restore):
    from collections import deque
    rules = rules_for(version)
    events = alphabet(with_restore)
    start = initial()
    frontier, seen, findings, transitions = deque([(start, ())]), {start}, {}, 0
    for _ in range(depth):
        nxt = deque()
        while frontier:
            w, trace = frontier.popleft()
            for ev in events:
                transitions += 1
                s = step(w, ev, rules, version, interp)
                if s.verdict in ("conflict", "ambiguity", "out_of_store"):
                    if s.verdict == "conflict":
                        sig = (s.verdict, ev.kind, tuple(sorted(tuple(c) for c in s.conflict_sets)))
                    elif s.verdict == "ambiguity":
                        sig = (s.verdict, ev.kind,
                               tuple(sorted({("entry" if o.entry else "none", o.conf) for o, _ in s.passing})))
                    else:
                        sig = (s.verdict, ev.kind)
                    if sig not in findings:
                        f = _step_record(s)
                        f["trace"] = [e.label() for e in trace] + [ev.label()]
                        findings[sig] = f
                succ = list(s.passing)
                if s.verdict == "conflict":
                    least = min(len(v) for v in s.violations.values())
                    succ = [(o, apply(w, ev, check(w, ev), o, version["numbering"], interp))
                            for o, v in s.violations.items() if len(v) == least]
                for o, post in succ:
                    if post not in seen:
                        seen.add(post)
                        nxt.append((post, trace + (ev,)))
        frontier = nxt
    return {"depth": depth, "with_restore": with_restore, "states": len(seen),
            "transitions": transitions, "findings": list(findings.values())}


def run(inputs):
    vname = inputs["version"]
    if vname not in VERSIONS:
        raise InputError(f"unknown version {vname!r}")
    version = VERSIONS[vname]
    interp = dict(ENTRY_DEFAULT_READINGS)
    extra = set(inputs["interpretation"]) - set(interp)
    if extra:
        raise InputError(f"unknown readings {sorted(extra)}")
    interp.update(inputs["interpretation"])
    mode = inputs["mode"]
    head = {"version": vname, "version_sha": version["sha"], "interpretation": interp}
    if mode.get("kind") == "explore":
        res = _explore(version, interp, int(mode["depth"]), bool(mode.get("with_restore", False)))
        return {"observation": {"kind": "explore", **head},
                "analysis": {"kind": "explore", **head, **res}}
    if mode.get("kind") != "trace":
        raise InputError(f"unknown mode {mode!r}")
    setup = [_event(e) for e in inputs["initial"].get("setup_events", [])]
    events = [_event(e) for e in inputs["events"]]
    w, setup_failure, recs = _trace(version, interp, setup, events)
    if setup_failure is not None:
        return {"observation": {"kind": "trace", **head, "setup_failure": setup_failure},
                "analysis": {"kind": "trace", **head, "setup_failure": setup_failure}}
    stopped = bool(recs) and recs[-1].verdict in ("conflict", "out_of_store")
    final = observe(w, None)
    obs = {"kind": "trace", **head,
           "answers": [[r.event.label(), r.checked.answer, list(r.checked.reasons)] for r in recs],
           "stopped_at_step": len(recs) - 1 if stopped else None,
           "final": final if not stopped else None}
    kinds = sorted({r.verdict for r in recs})
    ana = {"kind": "trace", **head, "steps": [_step_record(r) for r in recs],
           "classification": ("conflict" if "conflict" in kinds else "out_of_store" if "out_of_store" in kinds
                              else "ambiguity" if "ambiguity" in kinds else "consistent")}
    return {"observation": obs, "analysis": ana}
