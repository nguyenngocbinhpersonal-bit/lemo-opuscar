# Search Tools

`websearch.py` (free, unlimited) is the PRIMARY general-web search backend. Exa is
demoted to technical/code search only — it is optional and rate-limits on its free tier.

## websearch.py — general web search (primary)

Free, unlimited DuckDuckGo HTML search proxied through Jina Reader (`r.jina.ai`).
stdlib-only Python, no venv, no API key.

```bash
python D:\SOFTWARE\LOCAL_APP\YT_WF_001\.claude\skills\agent-reach\scripts\websearch.py "<query>" [--page N] [--region CODE] [--limit N] [--json]
```

### Capabilities (empirically verified 2026-09-19)

- Query is passed through **verbatim** — `site:`, `-site:`, `OR`, quoted phrases all
  honoured (DDG applies them natively): `site:reddit.com <topic>`, `"exact phrase"`,
  `keyword -site:pinterest.com`.
- CJK works via `--region`: `--region jp-jp` (Japanese, e.g. returns Nikkei),
  `--region kr-kr` (Korean, e.g. returns 국민연금연구원 statistics).
- Pagination via `--page N` (page 2 = `--page 1`, 0-indexed).
- Measured throughput: **18.5 queries/min unthrottled** (12 back-to-back queries,
  no sleep/pacing, 0 failures, 39.0s total, avg 3.25s/query, max 4.65s).
- `--json` emits `{"query","page","region","count","results":[{"title","url","snippet","date"}]}`.

### Exit codes (branch on these)

| Code | Meaning |
|---|---|
| 0 | at least one result returned |
| 3 | request succeeded, zero results parsed (query too narrow / no matches) |
| 4 | network/HTTP failure after retries |

### Hard dependency — do not "simplify" this

DuckDuckGo is called **only** through `https://r.jina.ai/<ddg-url>` — never
`html.duckduckgo.com` or `lite.duckduckgo.com` directly. A direct call is **not
network-blocked**: it reaches DuckDuckGo, and DDG's own anti-bot system answers
with `HTTP 202 Accepted` plus a challenge page instead of results —
`anomaly.js?sv=html&cc=botnet`, a `challenge-form`, the text "Unfortunately, bots
use DuckDuckGo too." and a nine-checkbox "Select all squares containing a duck:"
CAPTCHA.

Diagnosed 2026-09-19: DNS resolves normally (`20.43.161.105`, Azure) and the
response carries genuine nginx/DDG CSP headers, so this is not a firewall or a
regional filter. All four User-Agents tested (Chrome-spoofed, `curl/8.0`, none,
`agent-reach/1.0`) got the same 202 with zero results, so the classification is
**IP / TLS-fingerprint based, not header based** — there is no UA you can set that
fixes it, and a VPN is not the answer either (datacenter IPs are challenged
harder, not less).

Jina Reader works because the fetch originates from Jina's own datacenter
infrastructure, which DDG does not flag. Side-by-side on the identical URL:
direct → `HTTP 202`, CAPTCHA present, 0 results; via `r.jina.ai` → `HTTP 200`, no
CAPTCHA, 9 results. Jina Reader is therefore a **hard dependency** of this path.
If Jina Reader is down, general-web search via this script is down — there is
currently no independent fallback (see `shared/tools/registry.yaml`'s `web_search`
entry for the accepted-risk note and the documented escape hatch of self-hosting
SearXNG).

Also do not send a browser-spoofed `User-Agent` (e.g. a Chrome UA string) to
`r.jina.ai` — Cloudflare challenges it (403 "Just a moment..."); a plain
non-browser UA (curl's default, or Python's own `Python-urllib/x.y`) passes
cleanly. `websearch.py` is already built this way; don't "fix" the UA to look
more like a browser.

### Evaluated and rejected as a fallback: `ddgs` (2026-09-19)

`ddgs` 9.16.0 (metasearch over google / bing / brave / duckduckgo / mojeek /
startpage / yandex) was tested as a second backend precisely because it depends on
`primp`, which impersonates a browser's TLS fingerprint and therefore *does* get
past the challenge described above — at first. Measured on this machine, in order:

- first ~30 queries: works (8/10 on an unpaced 10-query burst, ~9 queries/min)
- after ~37 cumulative queries: collapses to **1/10** on `backend="duckduckgo"`
  **and** 1/10 on `backend="auto"`
- the collapse survives a fresh process, so it is server-side IP reputation, not
  in-process state
- at that same moment, `websearch.py` on the Jina path returned 5 URLs for 3/3 of
  the queries ddgs had just failed

`primp` buys a honeymoon of a few dozen queries, then the engines classify the IP —
which is exactly the volume one research run generates. It is a spare tyre, not a
second engine, so it is deliberately NOT wired in and `ddgs` is NOT a dependency of
this repo. It also carries per-engine ToS risk and an ongoing impersonation arms
race (the `duckduckgo_search` → `ddgs` rename history is a chain of such
breakages). Do not re-litigate this without fresh measurements.

### `uddg` unwrap

DDG wraps every organic result URL as `https://duckduckgo.com/l/?uddg=<urlencoded-real-url>&rut=...`.
`websearch.py` urldecodes the `uddg` param before returning results — otherwise
citations would record DDG's redirect URL instead of the real source. Sponsored
slots show up as `duckduckgo.com/y.js?...` (ad-click trackers, not the `/l/` redirect
format) and are dropped entirely rather than treated as organic results.

## Exa AI Search (optional, technical/code search only)

A high-quality AI search engine, good for finding technical docs, official examples,
and relevant web pages. Optional — use for technical/code lookups, not as the
general-web default (rate-limits on its free tier).

```bash
mcporter call exa.web_search_exa query="library API code example" numResults=5
```

### Use cases

| Scenario | Parameters |
|-----|------|
| Technical/code material | `web_search_exa(query: "framework name API example", numResults: 5)` |

> Exa MCP's `get_code_context_exa` is deprecated and not registered by default. For code questions, also use
> `web_search_exa`; when you need to search repo contents precisely, use the GitHub search in `dev.md` instead.

### Strengths

- Good at English-language content and technical docs
- Can locate official docs and code examples via query terms
- High-quality results

## Comparison with other search tools

| Tool | Source | Best for |
|-----|------|---------|
| websearch.py | agent-reach (scripts/) | General web search — primary, free, unlimited |
| Exa | agent-reach (optional) | Technical/code search only; free-tier rate-limited |
| Zhipu Search | my-mcp-tools | Chinese-language search |
| GitHub search | agent-reach (dev.md) | Repo/code search |
