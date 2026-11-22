#!/usr/bin/env python3
"""Send a build status message to a configured webhook."""

import json
import os
import sys
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def main():
    if len(sys.argv) != 2:
        raise SystemExit(f"Usage: {sys.argv[0]} MESSAGE")

    webhook = os.environ["BUILD_WEBHOOK"]
    message = sys.argv[1]
    parsed = urlparse(webhook)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise SystemExit("BUILD_WEBHOOK must be an HTTP(S) URL")
    request = Request(
        webhook,
        data=json.dumps(message).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request) as response:
        if response.status >= 400:
            raise SystemExit(f"webhook returned HTTP {response.status}")


if __name__ == "__main__":
    main()
