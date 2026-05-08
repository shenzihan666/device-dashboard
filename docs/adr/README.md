# Architecture Decision Records

An Architecture Decision Record (ADR) captures a significant technical decision along with its context and consequences. ADRs are **immutable** once accepted -- if a decision is reversed, a new ADR supersedes the original.

## Process

1. Copy the [ADR template](../templates/adr.md) into this folder.
2. Name it `NNN-short-title.md` using the next available number.
3. Fill in all sections; set status to **Proposed**.
4. Discuss with the team; update status to **Accepted** or **Rejected**.
5. Update the index table below and in [`docs/README.md`](../README.md).

## Statuses

| Status | Meaning |
|--------|---------|
| **Proposed** | Under discussion, not yet decided |
| **Accepted** | Decision is final and in effect |
| **Deprecated** | No longer relevant but kept for history |
| **Superseded** | Replaced by a newer ADR (link it) |

## Index

| ID | Title | Status | Date |
|----|-------|--------|------|
| [ADR-001](./001-react-flow-graph-engine.md) | React Flow as graph rendering engine | Accepted | 2025-01-15 |
