from __future__ import annotations

REPORT_SCHEMA = "spec_workbench_value_flow_coverage.v1"
CLOSURE_SCHEMA = "spec_workbench_value_flow_closure.v1"
CLOSURE_FILE = "70_value_flow_closure.json"
CLOSURE_STATUSES = frozenset({"open", "closed"})

# Where a required instant of a result comes from.
#   clock     the function samples the declared wall-clock accessor
#   argument  a parameter carries it (``via`` names the parameter)
#   stored    the record is read from storage with its instant already in it
#   callee    another function produces the record (``via`` names the function)
OUTPUT_SOURCES = frozenset({"clock", "argument", "stored", "callee"})

# Where a scalar argument of a constructing function ends up.
#   field      stored as ``to`` = <Model>.<field> of the constructed record
#   derived    folded into ``to`` = <Model>.<field> (an identity, a digest, a text)
#   key        selects an existing record by ``to`` = <Model>.<field>
#   guard      only compared or validated; nothing keeps it
#   forwarded  handed to ``to`` = <function>, which keeps or judges it
SINKS_WITH_FIELD = frozenset({"field", "derived", "key"})
INPUT_SINKS = SINKS_WITH_FIELD | {"guard", "forwarded"}


class ValueFlowError(ValueError):
    """The case or its value-flow closure cannot be inspected safely."""
