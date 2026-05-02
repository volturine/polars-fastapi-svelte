#!/usr/bin/env python3

import json
import sys
import time
import urllib.error
import urllib.request


BODY = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-03-26",
        "capabilities": {},
        "clientInfo": {"name": "skill-check", "version": "1.0.0"},
    },
}


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <server-url>", file=sys.stderr)
        return 1

    url = sys.argv[1]

    last = None
    for _ in range(12):
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(BODY).encode("utf-8"),
                method="POST",
                headers={
                    "content-type": "application/json",
                    "accept": "application/json, text/event-stream",
                },
            )
            with urllib.request.urlopen(req, timeout=5) as res:
                payload = res.read().decode("utf-8", "ignore")
                content_type = res.headers.get("content-type", "")
                session_id = res.headers.get("mcp-session-id")
                if res.status != 200:
                    last = f"unexpected status from {url}: {res.status}"
                elif "text/event-stream" not in content_type:
                    last = f"unexpected content-type from {url}: {content_type}"
                elif not session_id:
                    last = "missing mcp-session-id header"
                elif '"protocolVersion":"2025-03-26"' not in payload:
                    last = "initialize response missing expected protocolVersion"
                else:
                    print(f"playwright mcp initialize ok at {url}")
                    return 0
        except urllib.error.HTTPError as err:
            last = f"unexpected http status from {url}: {err.code}"
        except Exception as err:
            last = f"failed to reach {url}: {err}"
        time.sleep(1)

    print(last or f"failed to reach {url}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
