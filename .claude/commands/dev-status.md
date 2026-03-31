---
name: dev-status
description: Generate a comprehensive development status document for a feature/system. Produces a single-file reference covering design decisions, user stories with status tracking, data schemas, architecture, and implementation progress.
disable-model-invocation: true
allowed-tools: Read, Grep, Glob
---

# Development Status Document Generator

When the user invokes `/dev-status <feature-name>`, produce a comprehensive status document that serves as the **single source of truth** for that feature's design and implementation. The document should follow the structure and conventions below, adapted to the specific feature.

If `$ARGUMENTS` names an existing feature with a status doc, read and update it. Otherwise, create a new one.

## Output Location

Write to: `state/CURRENT_STATUS_<FEATURE>_DESIGN.md`

Ask the user where the feature directory should live if not obvious.

## Document Structure

Use this skeleton, adapting sections to the feature. Every section is numbered. Use `---` horizontal rules between major sections.

```markdown
# <Feature Name> — Current Status & Full Design

This file captures EVERYTHING discussed across all conversations, design docs,
prototypes, and Firebase data. It is the single reference going forward.

> **Companion files:** List any related docs (schemas, functions, screens, analytics, tests, dev plan).

---

## 1. What We're Building

One paragraph: what the feature is, who it's for, how it works at a high level.

**North star metric:** The single metric that defines success.

**MVP scope:** Concrete boundaries — what's in, what's out.

---

## 2. Integration Decision

Where does this live in the codebase? Which repos, collections, services, pages?
Include the **rationale** for the decision ("No separate codebase because: ...").

---

## 3. Subsystems & Paths

Break the feature into logical subsystems. For each:
- Describe the subsystem
- List the paths/flows users take through it
- Use tables for comparison (e.g., user types, states, modes)
- Use ASCII diagrams for state matrices

### 3.X User Stories by Path

For EACH path, create a user story table:

| # | User Story | Status |
|---|-----------|--------|
| A1 | Staff can do X | ✅ |
| A2 | System does Y automatically | ⚠️ (partial — reason) |
| A3 | User sees Z in the app | ❌ (Step N) |

Status icons:
- ✅ = Done and deployed/working
- ⚠️ = Partial (explain what's missing in parentheses)
- ❌ = Not built yet (reference the dev step if known)
- Empty = Not started, no plan yet

Group stories by path/role. Use prefixes: A1-A99 (path A), B1-B99 (path B), X1-X99 (admin/config), P1-P99 (portal), R1-R99 (role-specific like rewards).

---

## 4. Authentication & Authorization

What auth model does this use? Reuse existing roles or new ones?
Include the data structure (collection paths, fields).
State what's NOT being built ("No new roles for MVP").

---

## 5. What Exists Right Now

### Project files:
List all files with brief descriptions using tree format.

### External dependencies:
List all external services, APIs, tools this feature depends on.

---

## 6. What Was Validated

For each thing that was tested and confirmed working, include:
- What was tested
- Date tested
- The actual command/output (real terminal output, not invented)

---

## 7. What Success Looks Like

Concrete definition of done. Step by step: if you do X, Y happens, and you see Z.

---

## 8. Steps to Completion

| Step | Description | Status |
|------|------------|--------|
| 1 | ... | ✅ / ⚠️ / ❌ |

---

## 9. What Worked — Patterns to Follow

Numbered list of decisions and approaches that proved correct during this stage.
These are lessons for future stages. Include the reasoning, not just the rule.

---

## 10. Intentionally NOT Built Yet

Explicit list of things excluded from scope. Prevents scope creep.

---

## 11. Next Stage Preview

One paragraph: what comes after this stage and what stays the same.
```

## Writing Conventions

1. **Be exhaustive.** This document replaces all previous design docs. Anyone should be able to understand the entire feature from this one file.
2. **Track implementation status.** Every user story has a status icon. Update them as work progresses.
3. **Include rationale for decisions.** Don't just say what — say why.
4. **Use tables liberally.** Comparisons, schemas, permissions, user stories — all tables.
5. **Use code blocks for structures.** Collection schemas, flow diagrams, terminal output.
6. **Reference companion files.** If architecture docs exist, reference them but keep the overview here.
7. **Parenthetical status details.** When something is partial (⚠️), explain in parentheses what's missing. When something is not built (❌), reference which dev step it belongs to.
8. **Keep sections numbered.** Makes cross-referencing easy.
9. **State what's NOT being built.** Explicit scope exclusions prevent scope creep.
10. **Include real output.** When documenting validations, use actual terminal output, not invented examples.

## Process

1. **Research first.** Read existing code, docs, and state files to understand what's already built and decided.
2. **Ask about unknowns.** If critical design decisions haven't been made, list them as open questions rather than guessing.
3. **Start with the skeleton.** Fill in what you know, mark unknowns.
4. **Update incrementally.** When new work is done, update the status icons and "What Exists" section.
