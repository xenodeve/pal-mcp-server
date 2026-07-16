# Reports & research (fork)

Investigations, post-mortems, and research records for this fork. Engineer-audience; `file:line`
and commit SHAs welcome. One dated file per topic.

## Index

- [2026-07-16 — clink Antigravity model-override investigation](2026-07-16-clink-antigravity-model-override-investigation.md)
  — root cause + RESOLVED: `agy --print` swallowed `--model`; fixed by ordering + fail-closed (issue #2, `7e80e42`). This is a bug in *this fork's* clink code, so it lives here (referenced by [ADR 0002](../adr/0002-per-call-model-effort-per-backend.md)).

_(Delegation-**routing** research — the subagent delegation log, token-economics, and model×effort
capability matrix — lives with the skills that it calibrated, in
[xenodeve/xeno-skills `docs/research/`](https://github.com/xenodeve/xeno-skills/tree/main/docs/research),
not here. This repo's reports cover clink *code*.)_
