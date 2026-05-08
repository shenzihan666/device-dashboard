# Document Templates

Standardized templates for contributing to the project documentation. Copy the appropriate template into the target category folder, fill in all sections, and remove placeholder text before committing.

## Available Templates

| Template | Target folder | When to use |
|----------|---------------|-------------|
| [bug-report.md](./bug-report.md) | `docs/bugs/` | Documenting a confirmed bug or known issue |
| [feature-spec.md](./feature-spec.md) | `docs/features/` | Proposing or specifying new functionality |
| [adr.md](./adr.md) | `docs/adr/` | Recording a significant architecture or technology decision |
| [runbook.md](./runbook.md) | `docs/runbooks/` | Documenting an operational procedure |

## Naming Conventions

| Category | Pattern | Example |
|----------|---------|---------|
| Bug reports | `NNN-short-title.md` | `001-websocket-reconnect-loop.md` |
| Feature specs | `NNN-short-title.md` | `002-multi-tenant-auth.md` |
| ADRs | `NNN-short-title.md` | `002-sqlite-over-postgres.md` |
| Runbooks | `descriptive-name.md` | `incident-response.md` |

## Workflow

1. Copy the template into the correct folder.
2. Rename using the conventions above.
3. Fill in all sections; delete any that genuinely do not apply.
4. Update the category `README.md` index table.
5. Update [`docs/README.md`](../README.md) master index if needed.
6. Commit: `docs(category): short description`.
