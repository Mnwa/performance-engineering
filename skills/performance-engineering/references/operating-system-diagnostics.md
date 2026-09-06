# Operating-system and cloud diagnostics

Use after [systems-performance.md](systems-performance.md). Source IDs resolve
in [sources.md](sources.md). Commands are bounded, read-oriented examples for an
authorized Linux environment; they are not a script to run indiscriminately on
production. Tool availability, options, privileges, namespaces, and event
semantics must be verified on the actual host.

## Scope and safety first

Record the process, container, host, deployment revision, time window, CPU model,
core classes, effective resource limits, and workload. Establish whether the
observation comes from the host or a namespace. A guest does not necessarily see
host contention or physical topology. Keep an explicit list of visibility gaps.
[S01, S03]

Choose the least intrusive observation that can answer the hypothesis. Bound
capture duration, sample rate, file size, and cardinality; capture only authorized
processes. Stack traces, URLs, arguments, paths, and request payloads can contain
sensitive data. Redact and control retention. Do not automatically elevate
privileges, relax profiling restrictions, drop caches, change kernel tunables,
disable security mitigations, or run a disruptive load generator.

### A small Linux observation menu

Run only the commands needed for the diagnosis; collect timestamps alongside
results. Set `PID` to the intended process's positive numeric PID first.

```sh
# Basic scope and memory accounting; files/fields depend on kernel and permissions.
cat "/proc/$PID/cgroup"
cat "/proc/$PID/status"
cat "/proc/$PID/smaps_rollup"
cat /proc/meminfo

# Short pressure snapshot, where PSI is available.
cat /proc/pressure/cpu /proc/pressure/memory /proc/pressure/io

# Sysstat examples: five one-second reports; confirm local command options.
mpstat -P ALL 1 5
pidstat -u -r -d -w -p "$PID" 1 5
iostat -xz -y 1 5

# Supported events and permissions must be checked first.
perf stat -p "$PID" -e task-clock,context-switches,cpu-migrations,page-faults -- sleep 10
perf record -F 99 -g -p "$PID" -- sleep 10
```

The sampling rate and duration are illustrative, not overhead guarantees.
`smaps_rollup` walks memory mappings and can have cost. Sysstat's reports have
different scopes and units; these examples do not make their values comparable.
Treat `perf` attach scope and child/thread coverage as part of the experiment.
[T02, T05, O03, O09, O10, O11]

## CPU: capacity, scheduling, and actual work

Compare process/thread CPU time with elapsed time and valid completed operations.
Inspect per-CPU load and runnable delay before increasing workers. Look for a
single busy thread, migrations, contention, CPU quota, and mixed fast/slow cores.
Only then inspect instructions, branches, stalls, and execution dependencies.
Counter names and ratios are CPU-specific evidence, not universal diagnoses.
[S04, T02]

Check virtualized and containerized capacity explicitly. In cgroup v2,
`cpu.max` describes a quota and period, and `cpu.stat` exposes usage and throttling
information where supported. Check the hierarchy and effective cpuset, not just
the immediate cgroup. A permissive leaf may still have a constrained ancestor.
Take counter deltas over the same interval as the complaint. [O01]

Original example: `cpu.max` of `200000 100000` corresponds to an aggregate quota
of two CPU-seconds per second. It does **not** grant two dedicated physical cores,
promise low scheduler latency, or prove that any specific request was throttled.
A process with many workers can exhaust a period's quota while host-wide CPU
looks low. Correlate throttling and scheduling evidence with affected intervals;
more workers are not automatically the remedy.

Determine the real cgroup path using `/proc/$PID/cgroup` and the mounted hierarchy
visible to the observer. Do not blindly append a container-relative path to a
host path. Check namespace mappings and ancestors with appropriate access.

## Memory: distinguish ownership, residency, and pressure

Track application live bytes and retained capacities alongside process RSS/PSS
and the enclosing cgroup's memory. RSS is not live heap; sharing, file mappings,
stacks, and allocator retention complicate attribution. Do not add overlapping
process and cgroup figures as if they were separate allocations. [O03]

Use allocation profiles to identify ownership and lifetime; use system evidence
to test whether reclaim, faults, swapping, or limit enforcement affects latency.
In cgroup v2, inspect `memory.current`, relevant limits such as `memory.high` and
`memory.max`, and event counters. A limit event and an OOM kill are not the same
outcome. Memory pressure can hurt before a process is killed. [O01]

PSI describes time lost to resource pressure, with `some` and `full` meanings
that depend on the resource and scope. It is not a replacement for CPU
utilization, a heap profile, or request tracing. Correlate pressure windows with
application behavior; absence or lack of permissions must remain explicit. [O02]

For an allocation change, run a large burst followed by small requests and
quiescence. Record live bytes, retained scratch, residency, reuse, faults, and
tail latency over time. Trimming memory may improve headroom while increasing
future allocation and fault costs. See [allocations.md](allocations.md).

## Filesystem and block I/O: follow the whole path

Draw the path from application buffering through filesystem/page cache and
writeback to the device. Separate logical bytes from physical traffic, metadata
operations from bulk data, and read hits from misses. Track I/O size, latency,
queueing, errors, and achieved rate for the actual path. A buffered write's
completion is not necessarily the requested durability boundary. [S01, O09]

Device `%util` alone does not establish saturation for a parallel device such as
an SSD or an array. Test whether additional offered work increases useful rate
or only queueing and latency; check service concurrency and documented limits.
Likewise, a CPU's I/O-wait percentage is not a direct measure of device capacity.
[O09]

Benchmark the production durability contract, including flush or synchronization
where required. Do not quietly replace durable operations with buffered writes.
Avoid global cache eviction on a shared machine. Use a labeled cold-start test,
a controlled working set, or an isolated machine when a cold-cache comparison is
necessary; explain what is and is not cold.

## Network and remote dependencies

Separate application admission, connection-pool wait, name resolution,
connection/TLS setup, transfer, remote processing, and response consumption.
Look for excessive round trips, payload size, queue limits, retransmissions,
drops, and errors. Endpoint instrumentation is necessary because a local system
view alone cannot attribute remote service time. [S01, O06]

Test reused and new connections separately when both occur in production.
Changing connection counts can move contention downstream. Do not increase
socket buffers or pool sizes without a hypothesis, memory budget, and a
comparison that includes latency and failures. A faster server benchmark that
omits client decoding or delivery is not a complete user-flow result.

## Cloud comparison checklist

Compare equivalent workloads and constraints, not instance names alone. Record
resource allocation, storage/network limits, CPU architecture, region/topology,
replica count, autoscaling behavior, cold starts, and relevant burst/credit
policies from the deployment's provider documentation. Do not assume those
policies are identical across providers or unchanged over time.

Normalize both cost and CPU consumption by **valid useful output** at the target
latency and quality. Include idle capacity, retries, replication, and data
transfer when they are inside the chosen accounting boundary. A cheaper run
that drops more requests or relaxes output quality is not an equivalent result.
This accounting policy is a recommendation of this skill, not a benchmark from
either book.
