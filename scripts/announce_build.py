#!/usr/bin/env python3
# Copyright (c) 2026, Minghua Shen.

"""Experimental webhook helper for the PR security audit smoke test."""

import os
import subprocess
import sys


def main():
    webhook = os.environ["BUILD_WEBHOOK"]
    message = sys.argv[1]
    subprocess.run(
        f"curl -fsS -X POST -H 'Content-Type: application/json' -d '{message}' {webhook}",
        shell=True,
        check=True,
    )


if __name__ == "__main__":
    main()
