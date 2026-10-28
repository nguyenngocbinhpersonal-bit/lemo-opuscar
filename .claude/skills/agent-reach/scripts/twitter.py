#!/usr/bin/env python
"""Run `twitter` (twitter-cli) with the cookies saved by `agent-reach configure twitter-cookies`.

twitter-cli only reads TWITTER_AUTH_TOKEN / TWITTER_CT0 from its own process environment
(it does NOT read ~/.agent-reach/config.yaml, and falls back to browser-cookie extraction,
which fails here). This wrapper loads the two values from the agent-reach config on every
call and injects them into the child process ONLY -- nothing is exported to your shell, and
the values are redacted from anything echoed back.

Usage (all arguments are passed straight through to `twitter`):

    python <skill>/scripts/twitter.py search "query" --lang ja --since 2026-09-10 --min-likes 100 -n 10 --yaml
    python <skill>/scripts/twitter.py user-posts @someone -n 20 --yaml

Precedence: TWITTER_AUTH_TOKEN / TWITTER_CT0 already set in the environment win; otherwise
the config file is used. Config path: $AGENT_REACH_CONFIG, else ~/.agent-reach/config.yaml.

Exit codes: the child's own code; 2 = credentials missing; 3 = `twitter` executable not found.
stdlib only, no venv, no dependencies.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

KEYS = {"TWITTER_AUTH_TOKEN": "twitter_auth_token", "TWITTER_CT0": "twitter_ct0"}


def config_path() -> Path:
    override = os.environ.get("AGENT_REACH_CONFIG")
    return Path(override) if override else Path.home() / ".agent-reach" / "config.yaml"


def read_config_value(text: str, key: str) -> str:
    """Value of a top-level `key: value` line (optional quotes), or '' when absent."""
    m = re.search(rf"^[ \t]*{re.escape(key)}[ \t]*:[ \t]*(.*)$", text, re.M)
    if not m:
        return ""
    return m.group(1).split(" #")[0].strip().strip("\"'").strip()


def build_env(base: dict[str, str], cfg_text: str) -> dict[str, str]:
    env = dict(base)
    for env_name, cfg_key in KEYS.items():
        if not env.get(env_name):
            val = read_config_value(cfg_text, cfg_key)
            if val:
                env[env_name] = val
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


def redact(text: str, env: dict[str, str]) -> str:
    for env_name in KEYS:
        val = env.get(env_name)
        if val:
            text = text.replace(val, "***")
    return text


def main(argv: list[str]) -> int:
    cfg = config_path()
    cfg_text = cfg.read_text(encoding="utf-8", errors="ignore") if cfg.is_file() else ""
    env = build_env(os.environ, cfg_text)
    missing = [n for n in KEYS if not env.get(n)]
    if missing:
        print(
            f"twitter.py: missing {', '.join(missing)} -- not in the environment and not in {cfg}. "
            "Run `agent-reach configure twitter-cookies` (Cookie-Editor export) first.",
            file=sys.stderr,
        )
        return 2
    exe = shutil.which("twitter")
    if not exe:
        print("twitter.py: `twitter` (twitter-cli) not found on PATH -- `pipx install 'twitter-cli==0.8.5'`.", file=sys.stderr)
        return 3
    r = subprocess.run([exe, *argv], env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    sys.stdout.buffer.write(redact(r.stdout, env).encode("utf-8"))
    sys.stdout.flush()
    sys.stderr.buffer.write(redact(r.stderr, env).encode("utf-8"))
    sys.stderr.flush()
    return r.returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
