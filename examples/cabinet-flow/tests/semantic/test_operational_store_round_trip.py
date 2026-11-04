"""Durable lifecycle facts survive the operational store exactly as written.

A18 (waiting is truthful and survives restart) and A20 (the kernel keeps
evidence) rest on one property of the store: what a kernel module wrote is what
it reads back, including the facts that are written once — who retired a flow,
when and why, why a run was cancelled, why a delegation was revoked. The store
is lowered deterministically from `rules.persistence_backend`, so these
assertions need no running kernel: they bind the accepted models and the
accepted persistence closure to each other.
"""

from __future__ import annotations

import sqlite3

import pytest

from cabinet_flow.models import ActorRef, AgentDelegation, Flow, FlowRun, KernelInstant, ServiceTarget
from cabinet_flow.operational_store_persistence import (
    SqliteOperationalStoreRepository,
    create_operational_store_schema,
)

OWNER = ActorRef(actor_kind="owner", owner_principal_id="owner-1", delegation_id=None, channel=None)


@pytest.fixture()
def store():
    connection = sqlite3.connect(":memory:")
    create_operational_store_schema(connection)
    yield connection, SqliteOperationalStoreRepository(connection)
    connection.close()


def _flow(**changes) -> Flow:
    values = dict(flow_id="flow-1", name="Накладные", purpose="Сверить накладные с заказами", status="active",
                  created_by=OWNER, created_at=KernelInstant(epoch_us=1_700_000_000_000_001),
                  retired_by=None, retired_at=None, retirement_reason=None)
    return Flow(**{**values, **changes})


def test_an_active_flow_has_no_retirement_facts(store):
    _, repository = store
    repository.upsert_flow(_flow())
    stored = repository.load_flow("flow-1")
    assert stored == _flow()
    assert (stored.retired_by, stored.retired_at, stored.retirement_reason) == (None, None, None)


def test_retirement_facts_are_kept_exactly_as_written(store):
    _, repository = store
    repository.upsert_flow(_flow())
    retired = _flow(status="retired", retired_by=OWNER, retired_at=KernelInstant(epoch_us=1_700_000_000_999_999),
                    retirement_reason="Заменён новым флоу")
    repository.upsert_flow(retired)
    assert repository.load_flow("flow-1") == retired


def test_a_cancelled_run_keeps_its_reason_and_its_creation_instant(store):
    _, repository = store
    run = FlowRun(
        run_id="run-1", flow_activation_ref="activation-1", pinned_slot_activations=("slot-activation-1",),
        service_target=ServiceTarget(targets=("registry",), installation_ref="installation-1"),
        inputs=("value-1", "value-2"), initiated_by=OWNER, status="cancelled", waiting_on=(),
        in_flight_effect_attempts=(), outputs=(), created_at=KernelInstant(epoch_us=1_700_000_000_000_010),
        ended_at=KernelInstant(epoch_us=1_700_000_000_000_020), cancellation_reason="Владелец остановил запуск",
    )
    repository.upsert_flow_run(run)
    stored = repository.load_flow_run("run-1")
    assert stored == run
    assert isinstance(stored.inputs, tuple) and stored.created_at.epoch_us < stored.ended_at.epoch_us


def test_a_revoked_delegation_keeps_the_owner_reason(store):
    _, repository = store
    delegation = AgentDelegation(
        delegation_id="delegation-1", owner_principal_id="owner-1", agent_label="builder", channel="mcp",
        credential_binding_ref="credential-1", may_author=True, disclosure_ceiling="internal", status="revoked",
        issued_at=KernelInstant(epoch_us=1_700_000_000_000_100), revoked_at=KernelInstant(epoch_us=1_700_000_000_000_200),
        revocation_reason="Агент больше не нужен",
    )
    repository.upsert_agent_delegation(delegation)
    assert repository.load_agent_delegation("delegation-1") == delegation


def test_the_transaction_belongs_to_the_unit_of_work_not_to_the_store(store):
    connection, repository = store
    repository.upsert_flow(_flow())
    assert connection.in_transaction
    connection.rollback()
    assert repository.load_flow("flow-1") is None
