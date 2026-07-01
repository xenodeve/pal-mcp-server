# Fork changes

This is a fork of [BeehiveInnovations/pal-mcp-server](https://github.com/BeehiveInnovations/pal-mcp-server) (Apache-2.0). Everything from upstream is unchanged except for two additive `clink` agents described below — no existing CLI (`gemini`, `claude`, `codex`) behavior was touched.

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

## Known gotchas carried over from development

- **Config is cached at process start.** Any edit to `conf/cli_clients/*.json` or `clink/constants.py` needs a full MCP server restart before it takes effect — don't conclude a config fix didn't work until you've restarted and retried.
- **`command` must resolve in the *server's* process environment, not just your shell's.** A CLI that's on your interactive shell's `PATH` isn't automatically visible to a long-running or freshly-spawned server process depending on how it was launched — if a clink call fails with "not found in PATH" even though the CLI works fine in your terminal, swap the config's bare `command` (e.g. `"codex"`) for a full absolute path to the executable.
- **`antigravity`'s ConPTY approach is specific to the "silent under a pipe" problem `agy` has.** Don't copy the ConPTY pattern for other CLIs unless they have the same symptom (empty output, exit 0, under a plain pipe) — it adds a real dependency (`pywinpty`) and complexity that upstream's plain-pipe `base.py` path doesn't need for `gemini`/`claude`/`codex`.
