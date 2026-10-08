== curl ==
# curl -H "x-api-key: sk_…" "http://127.0.0.1:5000/api/shot?url=https://example.com&format=png&full=true" -o shot.png
# POST /api/keys  {"quota":1000}
# GET  /api/keys/1/usage
# CLI: shot https://example.com --key sk_… --full -o shot.png

== session plan ==
# Session 1: capture (playwright, local page) → tests
# Session 2: cache + quota + api → tests
# Session 3: web playground + cli → screenshots → README → CI/Docker/Pages → tag
