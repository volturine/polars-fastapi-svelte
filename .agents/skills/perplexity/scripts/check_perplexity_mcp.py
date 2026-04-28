#!/usr/bin/env python3

import json
import os
import pathlib
import subprocess
import sys
import time


INIT = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-03-26",
        "capabilities": {},
        "clientInfo": {"name": "skill-check", "version": "1.0.0"},
    },
}

TOOLS = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
EXPECTED = {
    "perplexity_search",
    "perplexity_ask",
    "perplexity_reason",
    "perplexity_research",
}


def send(proc: subprocess.Popen[str], payload: dict) -> None:
    assert proc.stdin is not None
    proc.stdin.write(json.dumps(payload) + "\n")
    proc.stdin.flush()


def read_json(proc: subprocess.Popen[str], timeout: float) -> dict:
    assert proc.stdout is not None
    start = time.time()
    while time.time() - start < timeout:
        line = proc.stdout.readline()
        if not line:
            time.sleep(0.1)
            continue
        line = line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    raise TimeoutError("no JSON-RPC response received")


def main() -> int:
    api_key_env = "PERPLEXITY_API_KEY"
    args = sys.argv[1:]
    if len(args) >= 2 and args[0] == "--api-key-env-var":
        api_key_env = args[1]
        args = args[2:]

    if len(args) != 1:
        print(f"usage: {sys.argv[0]} [--api-key-env-var NAME] <workdir>", file=sys.stderr)
        return 1

    api_key = os.environ.get(api_key_env)
    if not api_key:
        print(f"{api_key_env} is not set", file=sys.stderr)
        return 1

    root = pathlib.Path(args[0]).resolve()
    env = dict(os.environ)
    env["PERPLEXITY_API_KEY"] = api_key
    env.setdefault("PERPLEXITY_TIMEOUT_MS", "600000")
    proc = subprocess.Popen(
        ["npx", "-y", "@perplexity-ai/mcp-server"],
        cwd=root,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    try:
        send(proc, INIT)
        init = read_json(proc, 20)
        version = init.get("result", {}).get("protocolVersion")
        name = init.get("result", {}).get("serverInfo", {}).get("name")
        if version != "2025-03-26":
            print(f"unexpected protocolVersion: {version}", file=sys.stderr)
            return 1
        if name != "ai.perplexity/mcp-server":
            print(f"unexpected server name: {name}", file=sys.stderr)
            return 1

        send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        send(proc, TOOLS)
        tools = read_json(proc, 20)
        names = {item.get("name") for item in tools.get("result", {}).get("tools", [])}
        missing = EXPECTED - names
        if missing:
            print(f"missing expected tools: {', '.join(sorted(missing))}", file=sys.stderr)
            return 1

        print("perplexity mcp initialize ok and expected tools are present")
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


if __name__ == "__main__":
    raise SystemExit(main())
