"""Witness tests for accepted decision A20 (02_rules_installation.md).

One release fixes every ceiling and every dependency: each ceiling is one
release constant ``RELEASE_CEILING_<NAME>`` that nothing raises and no module
defaults a second time; over a ceiling is a refusal, never a truncation; and
the release pins every Python dependency and the sandbox runtime. Each test
carries the witness name its Required test declares.

The Factory project supplies the ``semantic_runtime`` pytest fixture. It binds
these scenarios to the generated public operations of State 5 — named here by
their operation names, with arguments shaped as the State 6 models — without
changing the assertions below. Each test gets a fresh, empty kernel store.

Fixture surface used here:

- ``issue_contract_version(slot_id, purpose, inputs, outputs,
  resource_bounds)`` -> contract_version_id (acts as agent ``author``; the
  bounds are sent as given);
- ``page_records(record_type, page_size=None)`` -> RecordPageAnswer;
- capabilities: ``host.set_env``, ``restart()``, ``mcp_request`` (with
  ``raw=``), ``installation.agent_token``, ``release``, ``kernel_sources()``.
"""

import ast
import json
import re
import sys
from pathlib import PurePosixPath

import pytest

TEXT = '{"type":"string"}'

# A20 rule 1, release v1
CEILINGS = {
    "wall_time_ms": 30000,
    "memory_bytes": 536870912,
    "output_bytes": 67108864,
    "process_count": 8,
    "sandbox_scratch_bytes_max": 268435456,
    "implementation_code_bytes_max": 1048576,
    "stored_value_bytes_max": 1048576,
    "trial_fixture_bytes_max": 67108864,
    "spool_file_bytes_max": 134217728,
    "spool_run_bytes_max": 536870912,
    "service_response_bytes_max": 134217728,
    "transport_timeout_ms": 60000,
    "surface_request_bytes_max": 134217728,
    "bounded_text_bytes_max": 16384,
    "failure_detail_bytes_max": 4096,
    "page_size_default": 50,
    "page_size_max": 200,
}
BOUNDS = ("wall_time_ms", "memory_bytes", "output_bytes", "process_count")

EXACT_VERSION = re.compile(r"\d+(\.\d+)*((a|b|rc)\d+)?(\.post\d+)?(\.dev\d+)?")
CPYTHON_312 = re.compile(r"(?i)cpython[ -]?3\.12\.\d+")


def _port(name, direction, schema, disclosure_class=None):
    return {
        "name": name,
        "direction": direction,
        "value_schema": schema,
        "carriage": "value",
        "media_type": None,
        "cardinality": "one",
        "disclosure_class": disclosure_class,
    }


def _issue(semantic_runtime, slot_id, purpose=None, **bounds):
    resource_bounds = {name: CEILINGS[name] for name in BOUNDS}
    resource_bounds.update(bounds)
    return semantic_runtime.issue_contract_version(
        slot_id,
        purpose=purpose or f"A20 witness: {slot_id}",
        inputs=[_port("x", "input", TEXT, "open")],
        outputs=[_port("y", "output", TEXT)],
        resource_bounds=resource_bounds,
    )


def _check_ceilings_hold(semantic_runtime, tag):
    """Six ceilings the kernel reads, each at its value and one unit over."""
    # A02 rules 1-2: every bound at its ceiling is accepted, each one unit over
    # is refused.
    _issue(semantic_runtime, f"a20_{tag}_at")
    for name in BOUNDS:
        with pytest.raises(Exception) as exc:
            _issue(
                semantic_runtime,
                f"a20_{tag}_over_{name}",
                **{name: CEILINGS[name] + 1},
            )
        assert exc.value.code == "refused", name

    # A16 rule 4: a string at `bounded_text_bytes_max` bytes is accepted, one
    # byte over is a field over its bound.
    at_bound = "p" * CEILINGS["bounded_text_bytes_max"]
    _issue(semantic_runtime, f"a20_{tag}_text_at", purpose=at_bound)
    with pytest.raises(Exception) as exc:
        _issue(semantic_runtime, f"a20_{tag}_text_over", purpose=at_bound + "p")
    assert exc.value.code == "invalid_request"

    # A16 rule 6: a page of `page_size_max` items may be asked, one more is
    # refused (State 5: invalid_request).
    page_size_max = CEILINGS["page_size_max"]
    slots = {
        s.slot_id
        for s in semantic_runtime.page_records("slot", page_size=page_size_max).records.slots
    }
    with pytest.raises(Exception) as exc:
        semantic_runtime.page_records("slot", page_size=page_size_max + 1)
    assert exc.value.code == "invalid_request"

    assert f"a20_{tag}_at" in slots and f"a20_{tag}_text_at" in slots
    assert f"a20_{tag}_text_over" not in slots
    assert not any(slot.startswith(f"a20_{tag}_over_") for slot in slots)


def _module_name(module_path):
    return PurePosixPath(str(module_path).replace("\\", "/")).with_suffix("").parts


def _ceiling_named(identifier):
    lowered = identifier.lower()
    return any(name in lowered for name in CEILINGS) or lowered == "page_size"


def _number(node):
    """The value of a numeric literal or of constant arithmetic over literals
    (``512 * 1024 * 1024``, ``1 << 20``), else None."""
    if isinstance(node, ast.Constant):
        value = node.value
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return value
        return None
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        operand = _number(node.operand)
        if operand is None:
            return None
        return -operand if isinstance(node.op, ast.USub) else operand
    if isinstance(node, ast.BinOp):
        left, right = _number(node.left), _number(node.right)
        if left is None or right is None:
            return None
        operations = {
            ast.Add: lambda a, b: a + b,
            ast.Sub: lambda a, b: a - b,
            ast.Mult: lambda a, b: a * b,
            ast.Pow: lambda a, b: a**b if abs(b) <= 64 else None,
            ast.LShift: lambda a, b: a << b if isinstance(a, int) and 0 <= b <= 64 else None,
        }
        operation = operations.get(type(node.op))
        return operation(left, right) if operation else None
    return None


def _bindings(statements):
    """(name, value node) of names and attributes bound by these statements."""
    found = []
    for node in statements:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                name = getattr(target, "id", None) or getattr(target, "attr", None)
                if name:
                    found.append((name, node.value))
    return found


def _definitions(source):
    """(name, value node) of every definition a module makes.

    Module and class level bindings, and parameter defaults; a local variable
    inside a function body is not a definition.
    """
    tree = ast.parse(source)
    found = _bindings(tree.body)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            found.extend(_bindings(node.body))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            arguments = node.args
            positional = arguments.posonlyargs + arguments.args
            with_default = positional[len(positional) - len(arguments.defaults):]
            pairs = list(zip(with_default, arguments.defaults)) + [
                (arg, default)
                for arg, default in zip(arguments.kwonlyargs, arguments.kw_defaults)
                if default is not None
            ]
            found.extend((arg.arg, default) for arg, default in pairs)
    return found


def _ceiling_definitions(source):
    """(name, value) of every ceiling-named number a module defines."""
    return [
        (name, _number(value))
        for name, value in _definitions(source)
        if _ceiling_named(name) and _number(value) is not None
    ]


# Ceiling values no module has another reason to hold: a definition of one of
# them outside the data provider is a second default under another name.
# (Small or common sizes — 8, 50, 200, 4096, 16384, 1 MiB — are left out.)
DISTINCT_CEILING_VALUES = {
    CEILINGS[name]
    for name in (
        "wall_time_ms",
        "memory_bytes",
        "output_bytes",
        "sandbox_scratch_bytes_max",
        "service_response_bytes_max",
        "transport_timeout_ms",
    )
}


def _ceiling_valued_definitions(source):
    """(name, value) of every definition whose number is a distinct ceiling."""
    return [
        (name, _number(value))
        for name, value in _definitions(source)
        if _number(value) in DISTINCT_CEILING_VALUES
    ]


def _top_level_imports(source):
    names = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def _distribution_key(name):
    return re.sub(r"[-_.]+", "_", name).lower()


def test_ceiling_not_overridable_by_env(semantic_runtime):
    """[witness: verification:kernel_a20_ceiling_not_overridable_by_env]

    A20 Required test 1: changing an environment variable does not change any
    ceiling.
    """
    # Control: under the plain host environment the ceilings hold.
    _check_ceilings_hold(semantic_runtime, "plain")

    # A20 rule 1: no environment variable raises a ceiling. Every spelling a
    # module might read is set to double the release value for the next start.
    for name, value in CEILINGS.items():
        for variable in (
            f"RELEASE_CEILING_{name.upper()}",
            name.upper(),
            f"CABINET_KERNEL_{name.upper()}",
            f"KERNEL_{name.upper()}",
        ):
            semantic_runtime.host.set_env(variable, str(value * 2))
    assert semantic_runtime.restart().started is True

    # The same checks give the same answers.
    _check_ceilings_hold(semantic_runtime, "env")


def test_over_ceiling_refused_not_truncated(semantic_runtime):
    """[witness: verification:kernel_a20_over_ceiling_refused_not_truncated]

    A20 Required test 2: a request one byte over `surface_request_bytes_max` is
    refused.
    """
    ceiling = CEILINGS["surface_request_bytes_max"]
    request = {
        "slot_id": "a20_over_request",
        "purpose": "A20 witness: over the request ceiling",
        "inputs": [_port("x", "input", TEXT, "open")],
        "outputs": [_port("y", "output", TEXT)],
        "resource_bounds": {name: CEILINGS[name] for name in BOUNDS},
    }
    body = json.dumps(request, separators=(",", ":")).encode("utf-8")

    def sized(size):
        # Trailing whitespace keeps the JSON valid: cutting the request back to
        # the ceiling would leave a well-formed request, so only a refusal —
        # never a truncation — keeps the slot from being created.
        return body + b" " * (size - len(body))

    author_token = semantic_runtime.installation.agent_token("author")

    # A20 rule 2, A16 rule 1: one byte over is refused, before anything else.
    with pytest.raises(Exception) as exc:
        semantic_runtime.mcp_request(
            "issue_contract_version", request, token=author_token, raw=sized(ceiling + 1)
        )
    assert exc.value.code == "invalid_request"
    slots = semantic_runtime.page_records("slot").records.slots
    assert "a20_over_request" not in {s.slot_id for s in slots}

    # Control: at exactly the ceiling the size check passes and the next check
    # decides — an unknown token gets the token refusal (A16 rule 1), so the
    # refusal above came from the one byte over.
    unknown_token = "u" * 43
    with pytest.raises(Exception) as exc:
        semantic_runtime.mcp_request(
            "issue_contract_version", request, token=unknown_token, raw=sized(ceiling)
        )
    assert exc.value.code == "unauthorized"


def test_ceilings_equal_release_constants(semantic_runtime):
    """[witness: verification:kernel_a20_ceilings_equal_release_constants]

    A20 Required test 3: every ceiling the kernel reads is the release constant
    `RELEASE_CEILING_<NAME>` with the value of the release table, and no module
    defines a second default.
    """
    # The generated release declares exactly the table of A20 rule 1.
    assert dict(semantic_runtime.release.ceilings) == CEILINGS

    sources = semantic_runtime.kernel_sources()
    providers = [path for path in sources if _module_name(path)[-1] == "data_provider"]
    assert len(providers) == 1
    provider = providers[0]

    # A20 rule 1: each ceiling is one data-provider constant with the table
    # value (70_data_provider_closure.json, module `data_provider`).
    constants = {}
    for name, value in _ceiling_definitions(sources[provider]):
        constants.setdefault(name, []).append(value)
    for name, value in CEILINGS.items():
        assert constants.get(f"RELEASE_CEILING_{name.upper()}") == [value], name
    assert all(
        name.startswith("RELEASE_CEILING_") for name in constants
    ), "the data provider holds no second spelling of a ceiling"

    # No other module binds a ceiling-named number, nor a ceiling's value
    # under another name (`MAX_BODY = 128 * 1024 * 1024`): no second default.
    second_defaults = {
        path: found
        for path, source in sources.items()
        if path != provider
        for found in [_ceiling_definitions(source) + _ceiling_valued_definitions(source)]
        if found
    }
    assert second_defaults == {}

    # Every ceiling constant the kernel names is one of the table's.
    named = set()
    for source in sources.values():
        named.update(re.findall(r"\bRELEASE_CEILING_[A-Z0-9_]+\b", source))
    assert named <= {f"RELEASE_CEILING_{name.upper()}" for name in CEILINGS}


def test_dependencies_pinned_by_release(semantic_runtime):
    """[witness: verification:kernel_a20_dependencies_pinned_by_release]

    A20 Required test 4: the release pins an exact version of every Python
    dependency and of the sandbox runtime, and the sandbox interpreter is
    CPython 3.12.
    """
    release = semantic_runtime.release

    # A20 rule 3: every pin is one exact version, never a range.
    dependencies = dict(release.dependencies)
    for name, version in dependencies.items():
        assert EXACT_VERSION.fullmatch(version), (name, version)

    # A20 rule 3: the sandbox interpreter is CPython 3.12, pinned to its patch.
    assert CPYTHON_312.fullmatch(release.sandbox_interpreter.strip())

    # Every third-party module the kernel imports is pinned by the release.
    sources = semantic_runtime.kernel_sources()
    own = {_module_name(path)[0] for path in sources}
    imported = set()
    for source in sources.values():
        imported.update(_top_level_imports(source))
    third_party = {
        name
        for name in imported
        if name not in sys.stdlib_module_names and name not in own and name != "__future__"
    }
    pinned = {_distribution_key(name) for name in dependencies}
    assert {name for name in third_party if _distribution_key(name) not in pinned} == set()
