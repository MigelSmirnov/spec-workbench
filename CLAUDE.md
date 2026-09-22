# Spec Workbench — agent entry point

Three commands, in this order. Do not search the repository, scan branches, or
choose tools from memory or filename prefixes.

```bash
python tools/workbench.py list            # curated projects + pipeline-resolved phase
python tools/workbench.py show <project>  # ref, path, phase, reading list, read order
python tools/authoring.py next <project> --json
```

`authoring next` returns:

- `phase` — the first not-ready authoring phase;
- `action` — the gate tool and args the pipeline will run;
- `findings` — deterministic blockers to resolve;
- `read` — the methodology documents that apply to this phase.

Read `AGENTS.md` and the documents in `read`. Nothing else is required before
acting on a phase. `PROJECT_INDEX.json` is the only source of project identity;
`skills/spec-authoring/authoring_sequence.json` is the only source of ordering
and per-phase reading. Future MCP wrappers call `tools/authoring_pipeline.py`
and must not implement a second sequence.

`ARTIFACTS` / `Artifacts:` in `workbench.py` output is a file-layout hint
(highest numbered design file, `global_spec.json` present). It is not the
authoring phase; an assembled project can still be blocked at State 7.

External plugin operations named `list_projects` (Cabinet, Registry, Factory)
are unrelated application data, never Spec Workbench project navigation.

`python tools/workbench.py status` is repository/index diagnostics only.

Generic tooling (`tools/`, `tests/`, `skills/`, `.github/`, `PROJECT_INDEX.json`)
changes only on `main` via a `tools/<topic>` branch. Project branches
(`agent/<project>`) own `examples/<project>/` and `experiments/` only.
