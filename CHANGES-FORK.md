# Fork changes

This is a fork of [BeehiveInnovations/pal-mcp-server](https://github.com/BeehiveInnovations/pal-mcp-server) (Apache-2.0), which has been **unmaintained since ~mid-2026**. Everything from upstream is unchanged except for the additive `clink` changes described below: two new agents (`antigravity`, `claude-9arm`) plus an optional **per-call `model` / `reasoning_effort` override**. Existing CLI (`gemini`, `claude`, `codex`) behavior is unchanged whenever the new params are omitted — they default to off.

## What was added

### `antigravity` — Google's Antigravity CLI (`agy`) as a clink agent

Google retired the Gemini CLI in mid-2026 in favor of Antigravity, a new closed-source Go binary invoked as `agy`. It only prints output when it thinks it's attached to a real terminal — a plain piped subprocess (the normal way every MCP server, including PAL, spawns a child CLI) gets back an empty stdout with exit code 0.

The fix is to drive `agy` through a real Windows pseudo-console (ConPTY) via [`pywinpty`](https://pypi.org/project/pywinpty/), so it believes it has a TTY and prints normally. New files:

- `clink/agents/antigravity.py` — spawns `agy` inside a ConPTY (`winpty.PtyProcess.spawn`) instead of the base agent's plain-pipe path. `clink/agents/base.py` is untouched, so this has zero effect on the other CLIs.
- `clink/parsers/antigravity.py` — strips the ANSI escape codes and CR/LF noise a real terminal introduces.
- `conf/cli_clients/antigravity.json` — preset config (`command: "agy"`, resolved via `PATH` at call time with a clear error if missing).
- `clink/constants.py` / `clink/agents/__init__.py` / `clink/parsers/__init__.py` — registration wiring for the new `runner="antigravity"` / `parser="antigravity_text"`.

**This is currently Windows-only** (ConPTY via `pywinpty`). On macOS/Linux, `agy` may work fine over a plain pipe — untested; if it needs a real PTY there too, `pywinpty` won't help (it's Windows-specific) and you'd want `pty.fork()`/`pexpect` instead.

Install: `irm https://antigravity.google/cli/install.ps1 | iex` (see Google's install docs for other platforms), then `clink cli_name="antigravity"` should work out of the box.

### `claude-9arm` — Claude Code CLI against an alternate model gateway (example)

`clink/agents/claude.py` (upstream) is already generic — it just spawns whatever `command` the config points to and appends a system prompt. So running Claude Code against a different OpenAI-compatible backend needs **no new code**, only a new config entry: point `command` at your `claude` binary and pass `--settings <path-to-a-settings-file-with-your-own-baseURL/apiKey>` plus `--model <the-gateway's-model-id>` via `additional_args`.

`conf/cli_clients/claude-9arm.json.example` ships as a template (renamed with a `.example` suffix so it isn't auto-loaded until you configure it — `clink`'s registry glob-discovers every `conf/cli_clients/*.json` file, and `_resolve_config()` raises uncaught if a JSON's `name` isn't a registered runner, so this example intentionally opts out until you're ready). `clink/constants.py` already has a `claude-9arm` entry (`runner="claude"`, same as the plain `claude` client) so the name resolves the moment you rename the file and fill in your paths.

To activate:
1. Copy `conf/cli_clients/claude-9arm.json.example` → `conf/cli_clients/claude-9arm.json`
2. Replace `command` with the absolute path to your `claude`/`claude.exe`
3. Replace the `--settings`/`--model` placeholders with your gateway's settings file path and model ID
4. Restart the MCP server (config is cached at process start, not read per-call)

### Per-call `model` + `reasoning_effort` override

Upstream `clink` fixes each CLI's model and reasoning at **config time** (`conf/cli_clients/*.json` args) — to vary them you had to edit the JSON and restart the server, or define a separate client per variant. This fork adds two **optional** clink tool params so a caller can choose the model + effort **per call**:

- `model` — overrides the model for this call. Mapped per CLI: **Codex** → `-m <model>`; everyone else (`claude` / `gemini` / `antigravity`) → `--model <model>`.
- `reasoning_effort` — **Codex only** (`low` | `medium` | `high` | `xhigh` | `max`), mapped to `-c model_reasoning_effort=<effort>`. Ignored by CLIs that bake effort into the model *name* (e.g. Antigravity's `"Gemini 3.5 Flash (High)"`, selected via `model`).

Both are optional and append **after** the config/role args, so a per-call value wins over any config default; omitting them reproduces the previous command byte-for-byte (backward-compatible). Implemented via a small `_model_args()` hook on the base agent that `CodexAgent` overrides.

Unlike the two agents above, this change **does** touch shared files — `clink/agents/{base,claude,codex,antigravity}.py` and `tools/clink.py` — but only additively (new optional kwargs + a schema field). New files: `tests/test_clink_model_effort.py` (asserts the per-CLI flag mapping + backward-compat).

Examples:
```
clink(cli_name="codex", model="gpt-5.6-sol",  reasoning_effort="max",  prompt="…")  # hardest leaf
clink(cli_name="codex", model="gpt-5.6-luna", reasoning_effort="high", prompt="…")  # cheap / quota-thrifty
clink(cli_name="antigravity", model="Claude Opus 4.6 (Thinking)",      prompt="…")  # non-OpenAI check
```

**Antigravity `--model` ordering (critical).** `agy`'s `--print` flag is **value-taking** — it
consumes the next token as the prompt. The naive order `agy --print --model "X" "<prompt>"`
makes `--print` swallow `--model` as its value, so `agy` runs with an empty model and silently
falls back to the persisted default (verified live: it reports *Gemini 3.5 Flash* regardless of
the requested model). `AntigravityAgent._build_command()` therefore places model options
**before** `--print` → `agy --model "X" --print "<prompt>"`, which live-testing confirmed makes
the requested model reach the backend. `AntigravityAgent.run()` also now **fails closed**:
`agy` exits non-zero (with a catalog error) on an unsupported model, so the runner raises instead
of returning the fallback as success. Covered by `test_antigravity_places_model_before_print`.

### Activate machine-local clients in `~/.pal/cli_clients/` (survives reinstalls, shared across installs)

Editing the bundled `conf/cli_clients/*.json` inside an installed package (site-packages) is
**ephemeral** — `uv tool install --force` / a `uvx` refresh overwrites it, and each install
location (uv-tool vs uvx) has its own copy. Instead, put machine-specific activations in the
**user config dir the registry already reads last (so it overrides the bundled config):
`~/.pal/cli_clients/*.json`** (`USER_CONFIG_DIR` in `clink/constants.py`; also honored:
`CLI_CLIENTS_CONFIG_PATH`). Configs there:

- **persist across reinstalls** (they're outside the package), and
- are read by **every** PAL instance on the machine — so a client activated once is available to
  both your editor's PAL (a `uv tool install`) and another tool's PAL (e.g. Codex's `uvx --from
  git+…` launch) with no per-install setup.

Use it for the two things the bundled config can't ship portably — an **absolute executable path**
(when the CLI isn't on the PAL process's `PATH`) and **activating `claude-9arm`** against your
gateway. Drop-in examples (fill in your own paths / model):

`~/.pal/cli_clients/antigravity.json` (absolute `agy` so it resolves regardless of PAL's PATH):
```json
{ "name": "antigravity", "command": "C:/…/agy.exe", "additional_args": [],
  "roles": { "default": { "prompt_path": "systemprompts/clink/default.txt", "role_args": [] } } }
```
`~/.pal/cli_clients/claude-9arm.json` (activate the Claude-Code-through-a-gateway client):
```json
{ "name": "claude-9arm", "command": "C:/…/claude.exe",
  "additional_args": ["--settings","C:/…/your-gateway.json","--model","<gateway-model-id>"],
  "roles": { "default": { "prompt_path": "systemprompts/clink/default.txt", "role_args": [] } } }
```
Keep `prompt_path` **relative** (`systemprompts/clink/…`) so it resolves against each install's own
package root, not a hard-coded location. Restart PAL after adding files (config is cached at start).

## Known gotchas carried over from development

- **Config is cached at process start.** Any edit to `conf/cli_clients/*.json` or `clink/constants.py` needs a full MCP server restart before it takes effect — don't conclude a config fix didn't work until you've restarted and retried.
- **`command` must resolve in the *server's* process environment, not just your shell's.** A CLI that's on your interactive shell's `PATH` isn't automatically visible to a long-running or freshly-spawned server process depending on how it was launched — if a clink call fails with "not found in PATH" even though the CLI works fine in your terminal, swap the config's bare `command` (e.g. `"codex"`) for a full absolute path to the executable.
- **`antigravity`'s ConPTY approach is specific to the "silent under a pipe" problem `agy` has.** Don't copy the ConPTY pattern for other CLIs unless they have the same symptom (empty output, exit 0, under a plain pipe) — it adds a real dependency (`pywinpty`) and complexity that upstream's plain-pipe `base.py` path doesn't need for `gemini`/`claude`/`codex`.
