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

## What was decided (owner, 2026-11-03)

The protection is against depending on the time by accident: functions are written by
the owner's agents and work on invoices and estimates, and the clock gives a function
nothing to leak. K-02 now says so. A stricter closure was built and checked on
2026-11-03: every door above closed, all semantic witnesses passing (commits `6209a76d`
to `1d3efc13`). It banned SQLite in functions and compiled the standard library from
source in every execution, and the owner took it back.

| Kept | Known and left open |
|---|---|
| `time.clock_gettime`, `time.thread_time`, `os.times` trapped; `datetime.datetime.now` concludes `sandbox_violation` | `_datetime`, SQLite, a fresh import of `time`, `resource.getrusage`, file timestamps |

The "after the change" column above is the stricter closure; only the kept row holds
now. Should functions by outside authors appear, this is where to start: commit
`1d3efc13` holds that closure's rule and its patch, and the kernel cannot make
`CLOCK_REALTIME` lie inside bubblewrap, so a real guarantee needs a runtime that controls
the clock, such as a WASI build. Randomness has the same class of doors and was not
measured. `validated_runner_patch.diff` is the patch for what was kept.
