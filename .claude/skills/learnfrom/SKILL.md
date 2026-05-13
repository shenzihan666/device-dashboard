---
name: learnfrom
description: >-
  Clone a third-party GitHub project into the current repo's `references/`
  folder and produce a focused learning plan for adapting techniques into
  the user's own project, with explicit clarification gates for focus
  aspect, reference depth (idea-only vs verbatim code reuse), and license
  compliance. Use when the user wants to study / learn from / borrow
  ideas from / reverse-engineer / reference an external open-source
  repository, mentions a GitHub URL to 参考 / 学习 / 借鉴 / 研究, asks how
  to adopt a pattern from another codebase, or revisits a previously
  cloned reference under `references/`. Always asks the user (in Chinese)
  for any unspecified parameter; never assumes focus, depth, or licensing
  intent. Keeps every cloned project as a long-lived reference indexed in
  `references/INDEX.md` so it keeps feeding the user's project across
  sessions. Interacts with the user in Chinese; this SKILL.md is in English.
---

# learnfrom (参考开源项目学习器)

A workflow for safely pulling another GitHub project into the current repo
as a long-lived reference and producing an actionable learning plan focused
on a specific aspect the user cares about.

## Output language

- **Talk to the user in Chinese (中文)** — every question, summary, plan,
  and status update.
- All files written under `references/` are also in Chinese.
- This SKILL.md is English (agent-facing only).

## Hard rules (do not violate)

1. **Never assume.** If the user has not provided a value for any of the
   seven parameters in Phase 1, ask via `AskQuestion` (or conversational
   Chinese if the tool is unavailable). Do not pick a default silently.
2. **Never reuse code without checking the license.** Phase 2's license
   probe is mandatory; Phase 5 must surface license + reference-depth
   implications before the user adopts any code.
3. **Never delete or rewrite files inside `references/<repo>/`** — it is
   a read-only mirror of upstream. All adaptations go into the user's
   own source tree.
4. **Never commit large clones to git by default.** Default is to add
   the reference path to `.gitignore`. Only commit (vendor / submodule)
   when the user explicitly chooses that path in Phase 1.6.
5. **The reference must remain re-usable across sessions.** Phase 6
   (Index + Meta) is mandatory, even for one-off "I just want to peek"
   requests — that's how the project keeps fueling the user's work later.

## Workflow (6 phases, TodoWrite-driven)

Materialise this todo list with `TodoWrite` before Phase 1, then mark
each phase `in_progress` immediately before and `completed` immediately
after — so the user can watch progress in Chinese:

```
- [ ] 1. Clarify — 7 parameters via AskQuestion (no defaults)
- [ ] 2. Clone & License probe — git clone + read LICENSE/README
- [ ] 3. Map — locate files relevant to the focus aspect
- [ ] 4. Analyse — extract patterns, dependencies, design decisions
- [ ] 5. Plan — write a learning/adaptation plan with license gates
- [ ] 6. Index — register in references/INDEX.md + write study-meta.md
```

---

## Phase 1: Clarify (no assumptions)

Ask the user (in Chinese) for each of these seven parameters that is not
already given. Use `AskQuestion` with structured options where possible.
Batch related questions into a single `AskQuestion` call when it makes
the form easier to fill out.

### 1.1 GitHub URL
If missing: `请提供要参考的 GitHub 项目地址（HTTPS 或 SSH 均可）。`

### 1.2 Focus aspect (学习焦点) — multi-select allowed
If missing, present these options:
- 整体架构（顶层模块划分、目录结构、数据流）
- 某个具体功能或模块（请补充模块名）
- 编码风格 / 设计模式
- 算法 / 核心技术实现
- 测试策略 / 测试结构
- 工程化（CI、构建、发布、Docker、Monorepo 等）
- 文档与开发者体验（README、贡献指南、Issue 模板）
- UI / UX / 前端组件
- 其他（请自由填写）

### 1.3 Reference depth (借鉴层级) — license-critical, single-select
- A. 只看思路（read-only inspiration，不复制任何代码）
- B. 借鉴模式 / 结构（自己重写实现，参考其设计）
- C. 改写片段（基于其代码改写，需保留 attribution）
- D. 直接复用代码（vendor 进自己的项目，需严格遵守 LICENSE）

Make it crystal clear that A/B are nearly always safe; C/D require the
license check in Phase 2 to be compatible with the user's own project
license.

### 1.4 Specific files / paths (optional)
`您是否已经知道感兴趣的具体文件或目录？如有请列出，没有就让我自己探索。`

### 1.5 Clone strategy
- 浅克隆 `--depth=1`（推荐，省盘）
- 完整历史（如想研究项目演化、commit 历史）

### 1.6 Git handling for the reference itself
- 加入 `.gitignore`（推荐：参考资料不随用户仓库提交）
- Vendor 进仓库（参考资料随仓库同步，体积更大）
- Git submodule（独立版本管理）

If the user picks "vendor" or "submodule", Phase 5 MUST re-emphasise
the license implications because the reference now ships with the
user's repo.

### 1.7 Reference root path
Default suggestion: `references/<repo-name>/` under the current
workspace root. Confirm with user; allow override (some users may
prefer `vendor/`, `third_party/`, etc.).

---

## Phase 2: Clone & License probe

After Phase 1 is confirmed:

1. Create `references/` if missing. If a folder with the same name
   already exists under the chosen root, do NOT overwrite — ask the
   user whether to (a) use the existing clone, (b) re-clone to a
   suffixed path, or (c) abort.
2. Clone:
   ```bash
   git clone <flags> <url> references/<repo-name>
   ```
   Where `<flags>` is `--depth=1` or empty per Phase 1.5.
3. Capture metadata (need these for Phase 6):
   ```bash
   cd references/<repo-name>
   git rev-parse HEAD                      # pinned commit
   git remote get-url origin               # canonical URL
   git log -1 --format='%cI %an'           # last commit time + author
   ```
4. Read the LICENSE file (try `LICENSE`, `LICENSE.md`, `LICENSE.txt`,
   `COPYING`, `COPYING.md` in that order). If none exists, treat as
   **proprietary / all-rights-reserved** — Reference Depth C/D becomes
   forbidden, escalate immediately and re-confirm with the user.
5. Read `README.md` (or top-level docs) for the project's own
   description of its architecture and intended use.
6. Apply Phase 1.6's git-handling choice:
   - `.gitignore` → append `references/<repo-name>/` (or `references/`
     if not already present) to the user's project `.gitignore`.
   - vendor → leave clone as-is (will be committed with the rest of
     the repo). Make sure the upstream LICENSE file is preserved
     in-tree.
   - submodule → re-clone using `git submodule add <url>
     references/<repo-name>`.

### License → reference-depth compatibility matrix

Show the user this table when their depth choice (1.3) might conflict
with the upstream license:

| User depth ↓ / Upstream license → | MIT / BSD / Apache-2.0 | LGPL | GPL / AGPL | Proprietary / none |
|-----------------------------------|------------------------|------|------------|--------------------|
| A. 只看思路                       | ✅                     | ✅   | ✅         | ⚠️ 法律灰区，慎重  |
| B. 借鉴模式                       | ✅                     | ✅   | ✅ (clean-room 实现可避免传染) | ❌ |
| C. 改写片段                       | ✅ (保留 attribution)  | ⚠️   | ❌ (会传染你的项目许可) | ❌ |
| D. 直接复用代码                   | ✅ (保留 LICENSE 文件) | ⚠️   | ❌ (强制 GPL-ify 你的项目) | ❌ |

If the matrix shows ❌ or ⚠️ for the user's chosen combination, **stop
and re-prompt** before proceeding to Phase 3.

---

## Phase 3: Map (locate focus-relevant files)

Goal: produce a focused list of files to study, **not** a full repo
dump.

1. For each focus aspect from Phase 1.2, run targeted searches inside
   `references/<repo-name>/` (use `Glob` / `Grep`, NEVER `find` / `rg`
   directly):
   - 整体架构 → tree top 2 levels, locate entry points (`main`,
     `index`, `server`, `app`), config files, Dockerfile, deployment
     manifests
   - 某个具体功能 → grep for function/class names, follow imports
   - 编码风格 → look for linter configs (`.eslintrc`, `ruff.toml`,
     `pyproject.toml`), `CONTRIBUTING.md`, code-of-conduct
   - 算法 / 核心技术 → identify core modules from README + entry
     points, then trace `import` graph
   - 测试策略 → find `tests/`, `conftest.py`, `jest.config`, GitHub
     Actions matrices
   - 工程化 → `.github/`, `Makefile`, `Dockerfile`, `scripts/`, CI
     configs, release workflow
   - 文档与 DX → `README`, `docs/`, `examples/`,
     `.github/ISSUE_TEMPLATE`
   - UI / UX → top-level routes, `components/`, screenshots referenced
     in README
2. Build a "focus file map" and show it to the user before going deep:
   ```
   focus = "测试策略"
   files = [
     "tests/conftest.py — fixture wiring (~120 行)",
     "tests/test_*.py — 38 个文件，平均 80 行",
     ".github/workflows/ci.yml — CI matrix (3 OS × 4 Py 版本)",
     ...
   ]
   ```
3. Cap at ~15 files per focus aspect. Prefer breadth over depth at
   this phase — Phase 4 will go deep.

---

## Phase 4: Analyse

Read the mapped files and extract:

- **What the project does well** for the focus aspect (concrete, with
  file citations like `path/to/file.py:42-67`).
- **Why the design works** — reasoning, trade-offs, hidden
  assumptions.
- **Dependencies** that make the technique work (libraries, language
  features, infra). List them so the user can check feasibility in
  their own stack.
- **Pitfalls** — things that look elegant but have known drawbacks
  (search the project's issues / TODO comments / known-issues
  sections in README).
- **Evolution clues** (only if Phase 1.5 = full history) —
  `git log -p --follow <file>` on the relevant files to see how the
  design changed over time.

Cite every claim with a file path + line range. No hand-waving.

---

## Phase 5: Plan (the deliverable)

Write the learning/adaptation plan to:
```
references/<repo-name>/LEARNING_PLAN.md
```

Use the template at [`templates/learning-plan.md`](templates/learning-plan.md)
as the structure. Key sections:

1. **学习目标** — restate Phase 1.2 focus + 1.3 depth verbatim.
2. **License & 合规说明** — concrete: which license, what attribution
   is required, what files must travel with adapted code, what the
   user's own project license forbids.
3. **核心收获** — 3-7 bullets, each with `path/to/file:Lstart-Lend`
   citation.
4. **可移植性评估** — for each takeaway: dependencies needed,
   estimated effort (S/M/L), risk level, fit-with-current-codebase
   score (1-5).
5. **落地步骤** — ordered TODO list with concrete file paths in **the
   user's own project** that would change.
6. **不建议照搬的地方** — anti-patterns, license-incompatible chunks,
   over-engineered parts.
7. **后续追问** — questions the user should answer to refine the
   plan (asked AS questions, not as assumptions).

Print a Chinese summary of the plan to the chat after writing the
file.

---

## Phase 6: Index (long-term reusability)

Two files maintain the long-term value of the reference. Both live
under `references/`:

### 6.1 `references/<repo-name>/.study-meta.md`
Per-project metadata. Use [`templates/study-meta.md`](templates/study-meta.md).
Records: URL, pinned commit, license, focus aspect (1.2), depth (1.3),
date, learning plan path, and a one-line "next-time pickup" note.

### 6.2 `references/INDEX.md`
The master index across all reference projects. Use
[`templates/INDEX.md`](templates/INDEX.md). Append a row for every
reference project; if `INDEX.md` does not exist, create it from the
template first. Keep the table sorted by most-recently-touched.

After both files are updated, tell the user (in Chinese) how to
revisit:

> 下次想继续参考此项目时，直接告诉我「再看一下 `<repo-name>`」或「继续学
> `<repo-name>` 的 <focus>」，我会读取 `references/INDEX.md` 和该项目
> 的 `.study-meta.md` 恢复上下文，无需重新克隆或重新提问。

---

## Re-reference workflow (subsequent sessions)

Triggered when the user says things like:
- 「再看一下 `<repo-name>`」
- 「继续学 `<repo-name>`」
- 「`<repo-name>` 那边怎么处理 X 的？」
- 「更新一下 `<repo-name>` 的参考」

Steps:

1. Read `references/INDEX.md` to confirm the project exists.
2. Read `references/<repo-name>/.study-meta.md` for context.
3. Read `references/<repo-name>/LEARNING_PLAN.md` for prior
   conclusions.
4. Ask the user (in Chinese) what specifically to do this time:
   - 回答某个具体问题（直接进入 Phase 4 局部探查）
   - 扩充新焦点（追加一轮 Phase 1.2 → 5，结果 append 到现有
     `LEARNING_PLAN.md`）
   - 拉取上游最新代码并 diff（`cd references/<repo> && git pull`，
     再 `git diff <pinned_commit>..HEAD` 输出关键变更摘要）
   - 评估是否可以"毕业"该参考（learning fully ported → 状态改为
     已归档）
5. Update `.study-meta.md` 的「上次结束时的接续点」并 bump
   `INDEX.md` 中该行的「最近更新」时间戳。

---

## Templates

- [`templates/INDEX.md`](templates/INDEX.md) — master index across all
  references
- [`templates/study-meta.md`](templates/study-meta.md) — per-project
  metadata
- [`templates/learning-plan.md`](templates/learning-plan.md) — the
  deliverable plan
