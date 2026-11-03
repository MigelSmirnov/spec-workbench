# Finding: a function can read the real time in the sandbox

Measured 2026-11-03 through the kernel, on `projects/cabinet_kernel` at code-factory
`1cdcf9e9`, with an implementation submitted and tried like any other. K-02 and A19
promise functions no clock.

| What the code calls | Accepted code | After the change |
|---|---|---|
| `time.clock_gettime`, `time.thread_time` | passed, real time | `sandbox_violation` |
| `os.times`, `resource.getrusage` | passed | `sandbox_violation` |
| `_datetime.datetime.now`, `_datetime.date.today` | passed, real time | `sandbox_violation` |
| SQLite `strftime('%s','now')` | passed, real time | `sandbox_violation` at `sqlite3.connect` |
| `sys.modules.pop('time'); import time` | passed, real time | `sandbox_violation` at the import |
| `st_mtime` by `os.stat`, `lstat`, `fstat`, `posix.stat`, `os.scandir`, `pathlib` on a scratch file, the code file, `/proc/self` | passed, real time | zero |
| `datetime.datetime.now`, `datetime.date.today` | `crashed` (`TypeError`: the trap took `self`) | `sandbox_violation` |
| `time.time`, `importlib.reload(time)`, open `/proc/uptime`, `subprocess` | `sandbox_violation` | the same |

`validated_runner_patch.diff` is the temporary patch these results come from. It proves
the rule can be implemented; it was discarded, because the code is generated.

## What remains

The traps are Python-level. The kernel cannot make `CLOCK_REALTIME` lie inside a
bubblewrap namespace, so the guarantee is the closed list: an entry point found missing
is a defect of the release (A03 rule 4). Known, not closed: a function can measure a
duration by counting its own work, and `threading` holds a `time.monotonic` it took
before the traps. Randomness has the same class of doors (`posix.urandom`,
`_random.Random`) and was not measured here.
