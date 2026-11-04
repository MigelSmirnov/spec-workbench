"""The kernel has one clock, and its two readings are different things.

`rules.time_source_policy`: every timestamp the kernel writes is one
`KernelInstant` read from `system_clock.now`; elapsed time is a raw monotonic
integer read from `system_clock.monotonic_ns`, never stored and never a
timestamp. Both operations are lowered deterministically, so the assertions
hold without a running kernel.
"""

from __future__ import annotations

import time

from cabinet_flow.models import KernelInstant
from cabinet_flow.system_clock import monotonic_ns, now


def test_now_is_the_host_wall_clock_as_a_kernel_instant():
    reading = now()
    assert type(reading) is KernelInstant and type(reading.epoch_us) is int
    assert abs(time.time_ns() // 1_000 - reading.epoch_us) < 3_600 * 1_000_000


def test_elapsed_readings_are_raw_monotonic_integers_and_never_instants():
    before = time.monotonic_ns()
    first, second = monotonic_ns(), monotonic_ns()
    after = time.monotonic_ns()
    assert type(first) is int and type(second) is int
    assert before <= first <= second <= after
    assert not isinstance(first, KernelInstant)
