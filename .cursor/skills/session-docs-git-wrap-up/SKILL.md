---
name: session-docs-git-wrap-up
description: >-
  Ends a coding session by reconciling every doc in the repo with the current
  codebase, running every git hook stage without skipping tests, committing,
  and pushing — creating a private remote when none exists. Use when the user
  asks to wrap up, sync docs, commit everything, run hooked tests, or push
  with a private repo. Language- and host-agnostic; works for Python/Node/Go/
  Rust/etc. and GitHub/GitLab/Codeberg.
---

# Session docs, hooks, git wrap-up

## Mandate (verbatim)

NOW doc what we have done(if not already done), and fix the previous wrong or incomplete docs (if there are any) and then sync the docs and then git commit everything. do not skip any hooked test, if the test is not up to date change or get rid of them, if the tests are reasonable, pass them. then push everything, if there is no git repo already, create one and push. make sure the repo is private.

## Phase 0 — Detect the project's toolchain (do this first)

Never hardcode `uv`, `npm`, `pre-commit`, or `gh`. Detect what this repo actually uses, then use those.

Read the relevant manifests with one batch of file reads / `git ls-files` and answer:

- **Package manager / runner.** Look for: `pyproject.toml` + `uv.lock` (uv) · `poetry.lock` (poetry) · `requirements*.txt` (pip) · `package.json` + lockfile (`pnpm-lock.yaml` → pnpm, `yarn.lock` → yarn, `bun.lockb` → bun, `package-lock.json` → npm) · `go.mod` (go) · `Cargo.toml` (cargo) · `Gemfile` (bundler) · `Makefile` / `justfile` / `Taskfile.yml` (make/just/task).
- **Hook framework.** `.pre-commit-config.yaml` (pre-commit) · `lefthook.yml` (lefthook) · `.husky/` (husky) · `.git/hooks/` raw scripts · CI-only (no local hooks).
- **Test runner.** `pytest`, `unittest`, `vitest`, `jest`, `go test`, `cargo test`, `rspec`, `mix test`, etc. — look in scripts in `package.json`, `pyproject.toml [tool.*]`, `Makefile`, or CI config.
- **Docs framework (if any).** `mkdocs.yml` · `docs/conf.py` (sphinx) · `docusaurus.config.js` · `mdbook` · `typedoc.json` · `astro.config` content collections. Generated docs may need a rebuild step.
- **Repo host.** `git remote -v` → `github.com` (use `gh`), `gitlab.com` (use `glab`), self-hosted, or none. If no host CLI is installed, fall back to UI + `git remote add`.
- **Default branch.** `git symbolic-ref refs/remotes/origin/HEAD` or `git remote show origin | rg 'HEAD branch'`. Fall back to `main`/`master` by inspection.
- **Monorepo?** Multiple `package.json` / `pyproject.toml` / `Cargo.toml` files → expect multiple READMEs and per-package CHANGELOGs.

Record what you found and use it for the rest of the phases. When this skill writes commands like `<run> pre-commit …`, substitute the actual runner you detected (`uv run`, `poetry run`, `pnpm exec`, `npx`, bare command, etc.).

## Phase 1 — Identify what changed in this session

Goal: know exactly which behaviors, files, or interfaces moved so docs can be reconciled against them.

1. Read the session transcript / current diff. Use `git status`, `git diff`, `git diff --stat <default-branch>...HEAD`, and `git log --oneline -20` to enumerate changes since the last push.
2. List **added**, **removed**, **renamed**, and **behavior-changed** items. Pay particular attention to:
   - new or removed top-level scripts / entry points / public APIs
   - renamed CLI flags, commands, environment variables, config keys
   - changed defaults, hook stages, dependencies, supported runtimes
   - new or removed reports, generated artifacts, output paths

If nothing of substance changed and docs already reflect reality, say so and stop — do not invent a CHANGELOG entry.

## Phase 2 — Inventory every doc in the repo

Build a complete list before editing anything. Do not assume only `README.md` and `CHANGELOG.md` need updating.

Run patterns like:

```bash
git ls-files '*.md' '*.mdx' '*.rst' '*.adoc' '*.txt' 2>/dev/null
git ls-files | rg -i '(^|/)(readme|changelog|history|releases?|contributing|architecture|design|adr|rfc|notes?|agents|claude|cursor)\b' \
  | rg -i '\.(md|mdx|rst|txt|adoc)$'
ls .cursor/rules/ AGENTS.md CLAUDE.md .cursorrules docs/ 2>/dev/null
```

Then add to the inventory (skip what doesn't exist):

- **Top-level**: `README.md`, `CHANGELOG.md` / `HISTORY.md` / `RELEASES.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `LICENSE`.
- **Project docs trees**: `docs/`, `wiki/`, `notes/`, `adr/`, `rfcs/`. Include rendered-doc sources (`docs/index.md`, `docs/conf.py`, `mkdocs.yml`).
- **Per-package READMEs in monorepos**: every `**/README*` under `packages/`, `apps/`, `crates/`, `services/`, `cmd/`, etc.
- **Agent / IDE guidance**: `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `.cursor/rules/*.md`, `.github/copilot-instructions.md`, `.windsurfrules`.
- **Domain reports** in any language: `*报告.md`, `*-postmortem.md`, `*-rfc.md`, `*-design.md`.
- **Configuration "docs"**: `.env.example`, `pyproject.toml` / `package.json` / `Cargo.toml` `description`/`keywords` fields, `mkdocs.yml` nav.
- **Module-level docstrings / file headers** that read like docs (often describe project layout and rot when files move).
- **README badges** (build status, version, coverage, license, package). Update if URLs / package names changed.

## Phase 3 — Reconcile each doc against reality

For every doc in the inventory, scan for these specific failure modes and fix what you find:

1. **Stale file references.** Cross-check every path mentioned in docs against `git ls-files`. Remove or update references to deleted files; add references to new ones; fix renames.
2. **Stale commands.** Re-read `Quick start` / `Usage` / `Development` sections. Verify every command resolves under the **detected** toolchain (Phase 0). Update flags, scripts, and entry points.
3. **Project-layout trees.** ASCII trees in READMEs rot fast. Diff the tree in the doc against `git ls-files` (top two levels). Update the tree, and update prose that names the files.
4. **Capability tables / feature lists.** If a feature was added, removed, or relocated this session, the corresponding row must change.
5. **CHANGELOG / release notes.** Add an entry under `Unreleased` (or today's date, whichever the project uses). Match the file's own headings (`Added` / `Changed` / `Deprecated` / `Removed` / `Fixed` / `Security`) and the project's commit-message style. If the project doesn't keep a CHANGELOG, don't introduce one — note the change in whatever release-notes channel the project uses, or skip.
6. **Cross-references between docs.** Every link from one doc to another must still resolve, and the target must still say what the source claims.
7. **Code examples / API snippets in docs.** Function names, flags, and return shapes shown in markdown must match current code. Grep the codebase for the example identifiers to confirm.
8. **Configuration docs.** `.env.example`, hook configs, CI configs — if a new env var, secret, or hook stage was introduced, document it; if one was removed, delete the mention.
9. **Anchor / link integrity.** Internal `#anchor` links and relative links (`./other.md`) must still resolve. Fix dead anchors.
10. **Terminology consistency.** Pick one term per concept and use it across all docs (don't mix synonyms for the same thing).
11. **Generated docs (if applicable).** If the project uses sphinx / mkdocs / docusaurus / typedoc / mdbook, rebuild after editing source. Don't commit only the source if the project tracks the built output (rare but exists).
12. **Monorepo sync.** When something at the workspace root changed, check whether per-package READMEs / CHANGELOGs also need to move.

When in doubt: edit the doc to match the code. Do not edit code to match the doc unless the user explicitly asks.

## Phase 4 — Tests and hooks (no skipping)

1. Run the full hooked workflow under the **detected** toolchain. Common shapes:
   - **pre-commit (Python or polyglot)**: `<run> pre-commit run --all-files` → `<run> pre-commit run --hook-stage pre-push --all-files`.
   - **husky / lint-staged (Node)**: `<pm> run lint && <pm> run test` (or whatever `package.json` scripts the husky hooks call). To exercise the actual hook, do an empty `git commit --allow-empty -m 'test'` on a throwaway branch only if needed.
   - **lefthook**: `lefthook run pre-commit && lefthook run pre-push`.
   - **No local hooks**: run the project's documented test/lint scripts directly.
2. Never use `--no-verify`, `--no-gpg-sign`, or `SKIP=…` unless the user explicitly approved it for this turn.
3. If a test fails:
   - First decide *why*. If the test still encodes correct intent, fix the code until it passes.
   - If the test is genuinely obsolete (the behavior it asserted was intentionally removed or replaced this session), update or delete it, and note that in the CHANGELOG / release notes.
   - Do not rationalize away a real failure to "ship the docs."
4. Re-run hooks/tests after any fix until everything passes cleanly.

## Phase 5 — Commit

1. Stage everything intended (`git add -A` is fine if the working tree is clean of unrelated junk; otherwise stage selectively).
2. **Match the project's commit-message convention.** Detect, don't assume:
   - Conventional Commits if `commitizen` / `commitlint` / `cz-conventional-changelog` is configured.
   - The repo's own `git log --oneline -20` style otherwise.
3. Prefer one focused commit when changes are tightly related; split into multiple when they are not (e.g. doc commit separate from a code-fix commit).
4. Pass the message via heredoc to keep formatting clean:

```bash
git commit -m "$(cat <<'EOF'
<type-or-prefix per project convention>: short summary in present tense

<optional body explaining why, not what>
EOF
)"
```

## Phase 6 — Push, with a private remote if needed

1. **If `origin` already exists**:
   - `git push` (or `git push -u origin HEAD` for a new branch).
   - Pre-push hooks must pass — don't bypass them.
2. **If there is no git repo at all**:
   - `git init -b main` (or `master` if that's the user's default).
   - Make an initial commit (after Phases 3–5).
3. **If there is a repo but no remote**: create a **private** remote, then push. Use whatever host CLI matches the user's platform:

   | Host        | Command                                                                                  |
   |-------------|------------------------------------------------------------------------------------------|
   | GitHub      | `gh repo create <name> --private --source=. --remote=origin --push`                      |
   | GitLab      | `glab repo create <name> --private && git remote add origin <url> && git push -u origin HEAD` |
   | Codeberg / Gitea | API call or UI; then `git remote add origin <url> && git push -u origin HEAD`        |
   | Self-hosted | UI / API to create as private; then `git remote add origin <url> && git push -u origin HEAD` |

   If no host CLI is installed and the user can't tell you which host to use, **stop and ask** rather than picking one.
4. **Verify privacy** before declaring done. Examples:
   - GitHub: `gh repo view --json visibility,isPrivate` → expect `"isPrivate": true`.
   - GitLab: `glab repo view --output json` → expect `visibility` ≠ `public`.
   - Other hosts: confirm via API or UI screenshot/text.
   If visibility is wrong, flip it (`gh repo edit --visibility private`, equivalents on other hosts) and verify again.

## Phase 7 — Final verification (don't skip)

Before reporting completion, confirm all of:

- [ ] `git status` is clean.
- [ ] `git log -1` shows the new commit on the expected branch.
- [ ] Remote is up to date (`git status` says "up to date with 'origin/…'").
- [ ] Repo visibility is private (or N/A because the user wanted local-only / public was explicitly requested).
- [ ] Every doc in the inventory either was updated this session or was verified to still be accurate.
- [ ] All hook stages / test suites passed without `--no-verify` / `SKIP=…`.

Report concisely: what was changed, what was checked-and-found-already-correct, the commit SHA, and the privacy confirmation.

## Anti-patterns

- Hardcoding `uv` / `npm` / `gh` instead of detecting the project's actual toolchain in Phase 0.
- Updating only `README.md` and `CHANGELOG.md` without inventorying the rest of the docs (per-package READMEs, ADRs, agent rules, generated docs).
- Treating any module named `sync.py` (or similar) as "doc sync" — read the file before assuming.
- Adding a CHANGELOG entry for changes that didn't actually happen this session, or introducing a CHANGELOG to a project that doesn't keep one.
- Bypassing hooks "just this once."
- Pushing first and then noticing the repo is public.
- Picking a host (GitHub vs GitLab vs self-hosted) on the user's behalf when there's no remote and you can't tell which they want.
- Calling the task done while `git status` still shows untracked or modified files.
