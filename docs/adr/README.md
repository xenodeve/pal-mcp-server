# Architecture Decision Records (fork)

Load-bearing, hard-to-reverse decisions for this fork. **Write a new ADR — never edit-to-reverse.**
An ADR supersedes; the old one stays as history. Read the relevant ADR before touching its area.
See `t4-engineering-records` for the format/discipline.

Write an ADR when a decision is costly to undo: a seam/interface, a data/format contract, a
platform dependency, a security boundary. A reversible implementation detail does not need one.

## Index

_(none yet — add `0001-<slug>.md` as decisions are made)_

Candidate decisions from this fork's history (record if/when they're revisited):

- Antigravity via a Windows **ConPTY** (`clink/agents/antigravity.py`) rather than a plain pipe —
  see `CHANGES-FORK.md` for the rationale.
- Per-call `model`/`reasoning_effort` mapped **per back-end** via a `_model_args()` hook, appended
  after config args (backward-compatible) rather than a shared flag.
- Antigravity model options placed **before** the value-taking `--print` + **fail-closed** on a
  non-zero exit — see `docs/reports/2026-07-16-clink-antigravity-model-override-investigation.md`.
- **Zero-setup executable discovery** + shipping `claude-9arm` active, with `~/.pal/cli_clients/`
  as the override escape hatch.
