# welike / data-information

Workspace root for WeCom data-platform tooling.

## Sub-projects

| Path | Stack | Purpose |
|---|---|---|
| [`connection-dashboard/`](./connection-dashboard) | Python 3.11+ (FastAPI) + React 19 (Vite) | Real-time dashboard tracking WeCom client ↔ AI server connections via Grafana Loki |

## Git hooks (pre-commit)

This repo uses the [pre-commit](https://pre-commit.com/) framework to enforce
fast, language-agnostic checks on every commit and push. The configuration
lives in [`.pre-commit-config.yaml`](./.pre-commit-config.yaml).

### One-time setup (new contributors)

```bash
# 1. Install the pre-commit runner (any one of these works)
pip install pre-commit          # or:  pipx install pre-commit
                                # or:  brew install pre-commit
                                # or:  conda install -c conda-forge pre-commit

# 2. Install the actual git hooks into .git/hooks/
pre-commit install --install-hooks
pre-commit install --hook-type commit-msg
pre-commit install --hook-type pre-push
```

That's it — every `git commit` and `git push` is now guarded.

### What runs when

| Stage | Hooks | Typical runtime |
|---|---|---|
| **pre-commit** | trailing whitespace · EOF newline · merge-conflict markers · large-file guard · YAML/TOML/JSON validity · case-conflict · private-key detection · LF line endings · **ruff** lint+format (Python) · **tsc --noEmit** (frontend) | < 5 s on staged files |
| **commit-msg** | [`conventional-pre-commit`](https://github.com/compilerla/conventional-pre-commit) — enforces `type(scope): subject` | < 1 s |
| **pre-push** | **pytest** (backend test suite) | a few seconds |

Hooks operate on staged files only (except pre-push tests, which always run on
the whole suite), are CI-friendly, and skip gracefully when optional toolchains
(`node_modules`, `.venv`) are absent.

### Conventional commit format

Commit messages must match:

```
<type>(<optional-scope>): <subject>
```

Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`,
`perf`, `ci`, `build`, `revert`.

Examples:

```
feat(connection-dashboard): add layout reset endpoint
fix(parser): handle missing serial field
docs: document hooks setup
chore(deps): bump ruff to 0.8.6
```

### Running hooks manually

```bash
pre-commit run --all-files       # everything, on every tracked file
pre-commit run ruff              # one specific hook id
pre-commit run --hook-stage pre-push --all-files   # simulate a push
```

### Updating hook versions

```bash
pre-commit autoupdate            # bumps `rev:` pins in .pre-commit-config.yaml
```

### Escape hatch

If a hook is blocking you for a legitimate reason (broken third-party tool,
WIP commit on a feature branch, etc.) you can bypass it for one operation:

```bash
git commit --no-verify -m "wip: ..."     # skip pre-commit + commit-msg
git push   --no-verify                   # skip pre-push
```

Use sparingly — CI will run the same checks and reject non-conforming commits.

### CI

The same configuration runs identically in CI with:

```bash
pre-commit run --all-files --show-diff-on-failure
```

Per-hook skipping is supported via the `SKIP` env var, e.g.
`SKIP=pytest-backend git push`.

## License

Proprietary — internal use only.
