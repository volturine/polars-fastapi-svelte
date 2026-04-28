from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STRICT_SCOPES = frozenset({'just-verify', 'just-test', 'just-test-e2e', 'just-test-frontend'})

DEFAULT_PATTERNS = [
    'Warning:',
    'Traceback',
    'UnhandledPromiseRejection',
    'DeprecationWarning',
    'ResourceWarning',
    'ERROR',
    'EPIPE',
    'ECONNRESET',
]


@dataclass(frozen=True)
class Match:
    pattern: str
    line_number: int
    line: str


def _load_allowlist(path: Path, scope: str) -> list[re.Pattern[str]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, list):
        raise ValueError('Allowlist must be a JSON array')
    allowlist: list[re.Pattern[str]] = []
    for item in data:
        if not isinstance(item, dict):
            raise ValueError('Allowlist entries must be objects')
        item_scope = item.get('scope')
        pattern = item.get('pattern')
        if not isinstance(item_scope, str) or not isinstance(pattern, str):
            raise ValueError('Allowlist entries must include string scope and pattern fields')
        if item_scope != scope:
            continue
        allowlist.append(re.compile(pattern))
    return allowlist


def _allowed(line: str, allowlist: list[re.Pattern[str]]) -> bool:
    return any(pattern.search(line) for pattern in allowlist)


def _scan(output: str, *, allowlist: list[re.Pattern[str]]) -> list[Match]:
    matches: list[Match] = []
    for line_number, line in enumerate(output.splitlines(), start=1):
        if _allowed(line, allowlist):
            continue
        for pattern in DEFAULT_PATTERNS:
            if pattern in line:
                matches.append(Match(pattern=pattern, line_number=line_number, line=line))
                break
    return matches


def _pipe_stream(stream: io.TextIOBase | None, target: io.TextIOBase, chunks: list[str]) -> None:
    if stream is None:
        return
    for line in stream:
        chunks.append(line)
        target.write(line)
        target.flush()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run a command and fail on unclassified warnings/errors in output.')
    parser.add_argument('--scope', required=True)
    parser.add_argument('--allowlist', default='packages/shared/config/warning-allowlist.json')
    parser.add_argument('--cwd')
    parser.add_argument('--report-only', action='store_true')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    return parser.parse_args()


def _scan_returncode(scope: str, returncode: int) -> list[Match]:
    if scope not in STRICT_SCOPES or returncode == 0:
        return []
    return [Match(pattern='NONZERO_EXIT', line_number=0, line=f'command exited with code {returncode}')]


def main() -> None:
    args = _parse_args()
    command = args.command
    if command and command[0] == '--':
        command = command[1:]
    if not command:
        raise SystemExit('No command provided')

    allowlist_path = ROOT / args.allowlist
    allowlist = _load_allowlist(allowlist_path, args.scope)
    command_cwd = ROOT / args.cwd if args.cwd else ROOT

    proc = subprocess.Popen(
        command,
        cwd=command_cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    stdout_thread = threading.Thread(
        target=_pipe_stream,
        args=(proc.stdout, sys.stdout, stdout_chunks),
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=_pipe_stream,
        args=(proc.stderr, sys.stderr, stderr_chunks),
        daemon=True,
    )
    stdout_thread.start()
    stderr_thread.start()
    returncode = proc.wait()
    stdout_thread.join()
    stderr_thread.join()

    combined = ''.join(stdout_chunks + stderr_chunks)
    matches = [*_scan(combined, allowlist=allowlist), *_scan_returncode(args.scope, returncode)]
    if not matches:
        raise SystemExit(returncode)

    print(f'warning scanner found {len(matches)} unclassified matches for scope {args.scope}', file=sys.stderr)
    for item in matches:
        print(f'  line {item.line_number}: [{item.pattern}] {item.line}', file=sys.stderr)

    if args.report_only and returncode == 0:
        raise SystemExit(0)

    raise SystemExit(returncode or 1)


if __name__ == '__main__':
    main()
