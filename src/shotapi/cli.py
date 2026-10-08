"""Command line client for shotapi.

    python cli.py --help
    python cli.py newkey --quota 1000
    python cli.py shot https://example.com --key sk_... --full -o shot.png
    python cli.py usage 1

Talks to a running instance (see README: python wsgi.py).
"""
import argparse
import json
import os
import urllib.error
import urllib.request

DEFAULT_BASE = os.environ.get("SHOTAPI_URL", "http://127.0.0.1:8000")

def _call(method, path, data=None, headers=None, base=None):
    req = urllib.request.Request((base or DEFAULT_BASE).rstrip("/") + path,
                                 data=data, method=method, headers=headers or {})
    with urllib.request.urlopen(req) as r:
        return r.status, dict(r.headers), r.read()

def cmd_shot(args):
    q = urllib.parse.urlencode({"url": args.url, "format": args.fmt, "full": str(args.full).lower()})
    try:
        status, headers, data = _call("GET", "/api/shot?" + q,
                                      headers={"x-api-key": args.key}, base=args.base)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace").strip()
        print("capture failed: HTTP %s %s" % (exc.code, body))
        if exc.code == 401:
            print("hint: create a key with 'python cli.py newkey' and pass it via --key")
        return 1
    with open(args.out, "wb") as f:
        f.write(data)
    print("HTTP %s %s %d bytes -> %s" % (status, headers.get("Content-Type", ""), len(data), args.out))
    return 0

def cmd_usage(args):
    try:
        status, headers, data = _call("GET", "/api/keys/%d/usage" % args.key_id, base=args.base)
    except urllib.error.HTTPError as exc:
        print("request failed: HTTP %s" % exc.code)
        return 1
    print("HTTP %s %s" % (status, data.decode().strip()))
    return 0

def cmd_newkey(args):
    payload = json.dumps({"quota": args.quota}).encode()
    try:
        status, headers, data = _call("POST", "/api/keys", payload,
                                      {"Content-Type": "application/json"}, args.base)
    except urllib.error.HTTPError as exc:
        print("request failed: HTTP %s %s" % (exc.code, exc.read().decode("utf-8", "replace")))
        return 1
    print("HTTP %s %s" % (status, data.decode().strip()))
    print("Store this key now - the API only returns it once.")
    return 0

def main(argv=None):
    p = argparse.ArgumentParser(prog="shot", description="shotapi command line client")
    p.add_argument("--base", default=DEFAULT_BASE, help="base URL of a running instance")
    sub = p.add_subparsers(dest="cmd")

    s = sub.add_parser("shot", help="capture a screenshot through the API")
    s.add_argument("url")
    s.add_argument("--key", required=True, help="x-api-key value")
    s.add_argument("--fmt", default="png", choices=["png", "jpeg"])
    s.add_argument("--full", action="store_true")
    s.add_argument("-o", "--out", default="shot.png")
    s.set_defaults(func=cmd_shot)

    u = sub.add_parser("usage", help="show quota usage for a key id")
    u.add_argument("key_id", type=int)
    u.set_defaults(func=cmd_usage)

    n = sub.add_parser("newkey", help="create a new API key")
    n.add_argument("--quota", type=int, default=1000)
    n.set_defaults(func=cmd_newkey)

    args = p.parse_args(argv)
    if getattr(args, "func", None) is None:
        p.print_help()
        return 0
    return args.func(args)
