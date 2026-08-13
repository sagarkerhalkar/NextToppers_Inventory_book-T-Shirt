from __future__ import annotations

import argparse
import http.client
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Direct local HTTP probe without system proxy settings.")
    parser.add_argument("host")
    parser.add_argument("port", type=int)
    parser.add_argument("path")
    parser.add_argument("--expect", default="")
    parser.add_argument("--forbid", action="append", default=[])
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    connection = http.client.HTTPConnection(args.host, args.port, timeout=args.timeout)
    try:
        connection.request(
            "GET",
            args.path,
            headers={
                "Host": f"{args.host}:{args.port}",
                "User-Agent": "NextToppersInventoryHealthProbe/1.0",
                "Connection": "close",
            },
        )
        response = connection.getresponse()
        body = response.read(2 * 1024 * 1024).decode("utf-8", errors="replace")
    finally:
        connection.close()

    print(f"HTTP {response.status} {response.reason} from http://{args.host}:{args.port}{args.path}")
    if response.status < 200 or response.status >= 400:
        print(body[:1000], file=sys.stderr)
        return 2
    if args.expect and args.expect not in body:
        print(f"Expected marker not found: {args.expect}", file=sys.stderr)
        print(body[:1000], file=sys.stderr)
        return 3
    for forbidden in args.forbid:
        if forbidden in body:
            print(f"Forbidden external marker found: {forbidden}", file=sys.stderr)
            return 4
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"HTTP probe failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
