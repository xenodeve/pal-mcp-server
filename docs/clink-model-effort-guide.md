# clink model & reasoning-effort guide (fork)

A practical routing guide: **which CLI + model + effort to `clink` to for which task.** Pairs
with the fork's per-call `model` / `reasoning_effort` params (see
[CHANGES-FORK.md](../CHANGES-FORK.md) and [tools/clink.md](tools/clink.md)). Capability
figures are the **[Artificial Analysis](https://artificialanalysis.ai/models) Intelligence
Index (v4.1)** — a composite of 9 evals, frontier ≈ 60; snapshot **2026-07**, re-fetch before
relying.

## The core principle

You (the orchestrator) are the only **metered, context-bound** token pool. The subagents are
either **local + free/unlimited** (`claude-9arm` → Qwen) or **subscription/flat + rate-limited**
(`codex`, `antigravity`). So "cheaper" means **fewer of *your* tokens** — delegate big-input /
small-output / cheaply-verifiable work; pick the *back-end* by **latency × intelligence ×
subscription-quota**, not by its token count (which is free or flat). Constrain the returned
output ("return ONLY X") — the reply is *your* tokens.

## What you can invoke

| CLI (`cli_name`) | Models | How model+effort is selected |
|---|---|---|
| `codex` | `gpt-5.6-sol` (default), `gpt-5.6-luna`*, `gpt-5.5`* | `model` → `-m`; `reasoning_effort` → `-c model_reasoning_effort=` (low\|medium\|high\|xhigh\|max) |
| `antigravity` | Gemini 3.5 Flash / 3.1 Pro, **Claude Opus/Sonnet 4.6 (Thinking)**, GPT-OSS 120B (`agy models`) | `model` → `--model "<Name (Effort)>"` (effort is baked into the name) |
| `claude-9arm` | Qwen 3.6 35B A3B (local) | fixed at config; free + unlimited |

*`gpt-5.6-luna` / `gpt-5.5` require account access — verify with `codex -m gpt-5.6-luna`.

## Capability × effort (AA Intelligence Index v4.1)

Codex GPT-5.6 ships in size tiers **Sol > Terra > Luna**; effort moves the score a lot on a
fixed model:

| Model | low | medium | high | xhigh | max |
|---|---|---|---|---|---|
| **gpt-5.6-sol** | 49.5 | 53.5 | **56** | 58 | **59** |
| gpt-5.6-luna | 33 | 38 | 46 | 49 | 51 |
| gpt-5.5 | 43.5 | 50.5 | 53 | 55 | — |
| *(Terra — dominated, skip)* | 40.5 | 45.5 | 49 | 51.5 | 55 |

Antigravity routes: **Claude Opus 4.6 = 53**, Sonnet 4.6 = 51, Gemini 3.5 Flash (high) = 50,
Gemini 3.1 Pro = 46, GPT-OSS 120B = 24. Local: **Qwen 3.6 35B A3B = 32**.

**On the efficient frontier only Luna (≤51) and Sol (≥53.5) survive** — Terra and GPT-5.5 are
each dominated by a Luna or Sol point (e.g. Sol `high` 56 beats Terra `max` 55 *and* is cheaper).

## Routing ladder

| Task | `clink` | Index |
|---|---|---|
| **Hardest leaf** (correctness-critical, edge-casey) | `codex` model=`gpt-5.6-sol` effort=`high`→`max` | 56–59 |
| **Quality default** (normal coding leaf) | `codex` model=`gpt-5.6-sol` effort=`low`→`medium` | 49.5–53.5 |
| **Quota-thrifty / bulk** | `codex` model=`gpt-5.6-luna` effort=`high`→`max`* | 46–51 |
| **Non-OpenAI second opinion** | `antigravity` model=`Claude Opus 4.6 (Thinking)` | 53 |
| **Free / unlimited mechanical bulk** | `claude-9arm` (Qwen) | 32 |
| **Skip (dominated)** | Terra, GPT-5.5, GPT-OSS 120B | — |

## Two rules that matter

1. **Effort has steep diminishing returns.** Sol `low→medium` = +4, but `xhigh→max` = +1 for
   roughly double the cost/latency. Use `medium`/`high` by default; reserve `max`/`xhigh` for
   the genuinely hardest task.
2. **Efficiency only matters under quota pressure.** Cost here is subscription **quota/rate-limit
   burn**, not money. For a one-off hard leaf you're not near the cap → just pick the intelligence
   you need. Luna's efficiency edge pays off for **high-volume** delegation, not single tasks.

## Examples

```
# hardest leaf — top intelligence
clink(cli_name="codex", model="gpt-5.6-sol", reasoning_effort="max", prompt="…")

# cheap / quota-thrifty leaf
clink(cli_name="codex", model="gpt-5.6-luna", reasoning_effort="high", prompt="…")

# a non-OpenAI check (effort is in the model name for antigravity)
clink(cli_name="antigravity", model="Claude Opus 4.6 (Thinking)", prompt="…")

# free, unlimited, mechanical — no subscription burn
clink(cli_name="claude-9arm", prompt="…")
```

Omit `model`/`reasoning_effort` to use whatever the CLI's `conf/cli_clients/*.json` pins.
