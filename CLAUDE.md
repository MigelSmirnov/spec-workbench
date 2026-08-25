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

Use the returned `canonical_ref`, `path`, and `read_order`. Only then inspect project files or switch branches.

`PROJECT_INDEX.json` is the curated source of Spec Workbench project identity.

`python tools/workbench.py status` is only for explicit repository/index diagnostics. Do not use exhaustive branch scanning for normal project discovery.

Never substitute external plugin operations such as Cabinet/Registry/Factory `list_projects` for this repository command.

After project resolution, follow `AGENTS.md` and any project-local `AGENTS.md` for design methodology and change rules.
