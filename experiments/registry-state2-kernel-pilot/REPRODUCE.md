# How to reproduce

## A. Locally, without a Kernel (control)

```bash
cd spec-workbench            # branch ccr-355d0166-9mky84
python experiments/registry-state2-kernel-pilot/adapter/build.py      # bundle; prints its sha256
python experiments/registry-state2-kernel-pilot/cases/make_cases.py   # the exact input cases
python experiments/registry-state2-kernel-pilot/run_local.py          # bundle vs the original model; fills expected outputs
```

`run_local.py` loads the bundle the way the Kernel's runner does: not entered
in `sys.modules`.

## B. A local Kernel from the promoted code

What this pilot did. It needs:
- Linux with bubblewrap 0.9.0;
- Python 3.12 with pydantic.

```bash
apt-get install -y bubblewrap
python3.12 -m venv kvenv && kvenv/bin/pip install pydantic==2.13.5
# installation file: owner-only mode 0600, data directory mode 0700, a git repository
# whose manifest/ directory may be empty; tokens for the owner, an agent "author" with
# may_author=true and an agent "reviewer" without it; mcp_listen_address 127.0.0.1:8930
cd code-factory/projects/cabinet_kernel
../../../kvenv/bin/python -m cabinet_kernel.surface /abs/path/installation.json
```

Then, from spec-workbench:

```bash
python experiments/registry-state2-kernel-pilot/run_kernel.py \
    --kernel http://127.0.0.1:8930 --author-token-file <author.token> --label local-034b50c
python experiments/registry-state2-kernel-pilot/compare.py --label local-034b50c
python experiments/registry-state2-kernel-pilot/finding/repro.py \
    --kernel http://127.0.0.1:8930 --author-token-file <author.token>
```

`run_kernel.py` is safe to run again. Equal contract versions, cases and
implementations are returned, not duplicated (A01 rule 4). An equal
implementation reuses its verdict (A04 rule 2).

## C. The owner's running Kernel

The owner's Kernel listens on `127.0.0.1:8830`. An author agent's token is in
`~/.cabinet-kernel/agent.token`, and the installation is in
`~/.cabinet-kernel/installation.json` (tools/kernel_scenarios/README.md). On
that computer:

```bash
python experiments/registry-state2-kernel-pilot/run_kernel.py \
    --kernel http://127.0.0.1:8830 --author-token-file ~/.cabinet-kernel/agent.token \
    --label owner-<deploy-id>
python experiments/registry-state2-kernel-pilot/compare.py --label owner-<deploy-id>
```

This creates the two `exp_registry_audit_*` slots there, with their
activations. Records are append-only, so the owner should agree to that first.
The agent token needs `may_author: true`.

## D. Recover a result as another author

```bash
python experiments/registry-state2-kernel-pilot/reproduce.py --kernel http://127.0.0.1:8930 \
    --token-file <reviewer.token> --slot exp_registry_audit_probe --index 3 --retry-in-kernel --out /tmp/r
```

Only the slot id and a non-author agent token are needed. The script reads
everything else through `get_repair_view`.
