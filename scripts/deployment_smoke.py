#!/usr/bin/env python3
"""Small post-deploy smoke check for a DomoNest deployment."""

from __future__ import annotations

import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class SmokeFailure(RuntimeError):
    pass


def fetch(url: str, *, timeout: float) -> tuple[int, object, bytes]:
    request = Request(
        url,
        headers={
            "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
            "User-Agent": "DomoNest-deployment-smoke/1.0",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310
            return response.status, response.headers, response.read()
    except HTTPError as exc:
        body = exc.read()
        raise SmokeFailure(f"{url} returned HTTP {exc.code}: {body[:300]!r}") from exc
    except URLError as exc:
        raise SmokeFailure(f"{url} could not be reached: {exc.reason}") from exc


def require_security_headers(headers: object) -> None:
    expected = {
        "x-content-type-options": "nosniff",
        "referrer-policy": "strict-origin-when-cross-origin",
    }
    for name, expected_value in expected.items():
        actual = headers.get(name, "")
        if expected_value.lower() not in actual.lower():
            raise SmokeFailure(f"Expected {name} to contain {expected_value!r}, got {actual!r}.")

    if not headers.get("strict-transport-security"):
        raise SmokeFailure("Missing Strict-Transport-Security header.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url", help="Deployment root, e.g. https://domonest.onrender.com")
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    parsed = urlparse(base_url)
    if parsed.scheme != "https" and parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise SmokeFailure("Remote deployment smoke checks require an https:// URL.")

    status, headers, body = fetch(f"{base_url}/health/", timeout=args.timeout)
    if status != 200:
        raise SmokeFailure(f"/health/ returned unexpected HTTP {status}.")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise SmokeFailure("/health/ did not return valid JSON.") from exc
    if payload != {"status": "ok"}:
        raise SmokeFailure(f"/health/ returned unexpected payload: {payload!r}.")
    if "no-store" not in headers.get("Cache-Control", ""):
        raise SmokeFailure("/health/ must send Cache-Control: no-store.")

    status, root_headers, _ = fetch(f"{base_url}/", timeout=args.timeout)
    if not 200 <= status < 400:
        raise SmokeFailure(f"/ returned unexpected HTTP {status}.")
    if parsed.scheme == "https":
        require_security_headers(root_headers)

    print(f"Deployment smoke passed: {base_url}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SmokeFailure as exc:
        print(f"Deployment smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
