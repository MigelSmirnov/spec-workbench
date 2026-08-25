# Fresh-clone navigation validation

This branch fixes project navigation for agent sandboxes and external readers that clone only `main`.

Validated behavior:

1. create a repository with `main` and an indexed `agent/demo` branch;
2. clone it with `git clone --single-branch --branch main`;
3. confirm `origin/agent/demo` is absent;
4. fetch only `refs/heads/agent/demo:refs/remotes/origin/agent/demo`;
5. confirm the remote-tracking ref is available without fetching arbitrary branches.

The automated regression test in `tests/test_project_navigation.py` encodes the same scenario.
