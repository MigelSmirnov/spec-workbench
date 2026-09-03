# Spec Workbench — agent entry point

## STOP: resolve the working project first

Do **not** search the repository for `list_projects`, project tools, MCP tools, Factory projects, Registry projects, or Cabinet projects.

Those are different concepts and may return unrelated application data.

For **Spec Workbench project navigation**, always start with:

```bash
python tools/workbench.py list
```

If the user has already named a project, resolve it with:

```bash
python tools/workbench.py show <project>
```

`PROJECT_INDEX.json` is the curated source of Spec Workbench project identity.
Never substitute external plugin operations such as Cabinet/Registry/Factory
`list_projects` for this repository command.

## STOP: ask the common authoring pipeline what comes next

After the project is resolved, do **not** reconstruct the design-state workflow
from filenames, search for project-local tooling, or choose a gate from memory.
Run:

```bash
python tools/authoring.py next <project> --json
```

The authoring CLI resolves the project's canonical ref, materializes it for
read-only deterministic inspection, and returns the first not-ready authoring
phase plus its gate/findings.

The machine source of truth for ordering is:

```text
skills/spec-authoring/authoring_sequence.json
```

The transport-neutral API is `tools/authoring_pipeline.py`. Future MCP wrappers
must call that same API; they must not implement a second authoring sequence.

The generic pipeline promoted to `main` covers State 0 through Stage 9. Tools
under `tools/` change only on `main`; project branches own only their
`examples/<project>/` data.

`python tools/workbench.py status` is only for explicit repository/index
diagnostics. Do not use exhaustive branch scanning for normal project discovery.

After pipeline resolution, follow `AGENTS.md` and any project-local `AGENTS.md`
for semantic design and change rules.
