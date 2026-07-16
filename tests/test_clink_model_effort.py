"""Per-call model + reasoning_effort override → CLI-specific flags.

Tests the pure command-building seam (`_build_command`): a clink call may pass
`model` / `reasoning_effort` and each agent maps them to its CLI's flags
(codex: `-m` + `-c model_reasoning_effort=`; others: `--model`). Omitting them
must leave the command untouched (backward compatible).
"""

from __future__ import annotations

from pathlib import Path

from clink.agents.base import BaseCLIAgent
from clink.agents.codex import CodexAgent
from clink.models import ResolvedCLIClient, ResolvedCLIRole


def _client(name: str, parser: str, runner: str | None = None) -> tuple[ResolvedCLIClient, ResolvedCLIRole]:
    prompt_path = Path("systemprompts/clink/default.txt").resolve()
    role = ResolvedCLIRole(name="default", prompt_path=prompt_path, role_args=[])
    client = ResolvedCLIClient(
        name=name,
        executable=[name],
        internal_args=[],
        config_args=[],
        env={},
        timeout_seconds=30,
        parser=parser,
        runner=runner,
        roles={"default": role},
        output_to_file=None,
        working_dir=None,
    )
    return client, role


def test_codex_maps_model_and_reasoning_effort():
    client, role = _client("codex", "codex_jsonl")
    agent = CodexAgent(client)
    cmd = agent._build_command(
        role=role, system_prompt=None, model="gpt-5.6-sol", reasoning_effort="high"
    )
    assert cmd == ["codex", "-m", "gpt-5.6-sol", "-c", "model_reasoning_effort=high"]


def test_codex_model_only_without_effort():
    client, role = _client("codex", "codex_jsonl")
    agent = CodexAgent(client)
    cmd = agent._build_command(role=role, system_prompt=None, model="gpt-5.6-luna")
    assert cmd == ["codex", "-m", "gpt-5.6-luna"]


def test_codex_effort_only_without_model():
    client, role = _client("codex", "codex_jsonl")
    agent = CodexAgent(client)
    cmd = agent._build_command(role=role, system_prompt=None, reasoning_effort="max")
    assert cmd == ["codex", "-c", "model_reasoning_effort=max"]


def test_base_agent_uses_model_flag_and_ignores_effort():
    # claude/gemini/antigravity take `--model`; effort is baked into the model name,
    # so a base agent ignores reasoning_effort.
    client, role = _client("gemini", "gemini_json")
    agent = BaseCLIAgent(client)
    cmd = agent._build_command(
        role=role, system_prompt=None, model="Gemini 3.5 Flash (High)", reasoning_effort="high"
    )
    assert cmd == ["gemini", "--model", "Gemini 3.5 Flash (High)"]


def test_no_overrides_leaves_command_unchanged():
    client, role = _client("codex", "codex_jsonl")
    agent = CodexAgent(client)
    assert agent._build_command(role=role, system_prompt=None) == ["codex"]


def test_antigravity_places_model_before_print():
    # agy's `--print` is VALUE-TAKING (it consumes the next token as the prompt), so
    # `--model` MUST precede `--print` or agy swallows it as the prompt and silently
    # falls back to the persisted default model. AntigravityAgent reorders so model
    # options come before `--print` (verified live: wrong order -> Gemini default,
    # right order -> the requested model reaches the backend).
    from clink.agents.antigravity import AntigravityAgent

    prompt_path = Path("systemprompts/clink/default.txt").resolve()
    role = ResolvedCLIRole(name="default", prompt_path=prompt_path, role_args=[])
    client = ResolvedCLIClient(
        name="antigravity",
        executable=["agy"],
        internal_args=["--print"],
        config_args=[],
        env={},
        timeout_seconds=30,
        parser="antigravity_text",
        runner="antigravity",
        roles={"default": role},
        output_to_file=None,
        working_dir=None,
    )
    agent = AntigravityAgent(client)
    cmd = agent._build_command(
        role=role, system_prompt=None, model="Claude Sonnet 4.6 (Thinking)"
    )
    assert cmd == ["agy", "--model", "Claude Sonnet 4.6 (Thinking)", "--print"]
    assert cmd.index("--model") < cmd.index("--print")
