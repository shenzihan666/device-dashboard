# Bug Reports

Structured tracking of known bugs and resolved issues. Each bug follows the [bug report template](../templates/bug-report.md).

## Severity Definitions

| Severity | Label | Description | Response expectation |
|----------|-------|-------------|---------------------|
| **P0** | Critical | System down, data loss, or security vulnerability | Immediate; drop everything |
| **P1** | High | Major feature broken, no workaround | Fix within current sprint |
| **P2** | Medium | Feature degraded but workaround exists | Schedule in next 1-2 sprints |
| **P3** | Low | Minor inconvenience, cosmetic, or edge case | Backlog; fix when convenient |

## Triage Workflow

```
Reported → Confirmed → Investigating → Fix in Progress → Resolved → Verified
                     ↘ Won't Fix / Duplicate
```

1. **Reported** -- Bug filed using the template.
2. **Confirmed** -- Reproduced by a second person or in CI.
3. **Investigating** -- Root cause analysis underway.
4. **Fix in Progress** -- PR open or committed.
5. **Resolved** -- Fix merged; update the bug doc with the commit/PR link.
6. **Verified** -- Confirmed fixed in production or staging.

## Process

1. Copy the [bug report template](../templates/bug-report.md) into this folder.
2. Name it `NNN-short-title.md` using the next available number.
3. Fill in all sections; assign a severity.
4. Update the index table below and in [`docs/README.md`](../README.md).

## Index

| ID | Title | Severity | Status | Date |
|----|-------|----------|--------|------|
| *No bugs documented yet* | | | | |
