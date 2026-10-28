"""websearch.py -- free, unlimited general-web search backend for agent-reach.

Routes DuckDuckGo HTML search results through the Jina Reader proxy
(https://r.jina.ai/), because html.duckduckgo.com / lite.duckduckgo.com are
BLOCKED direct from this machine (verified 2026-09-19: both GET and POST
return HTTP 202 with an empty body, or zero results). Jina Reader is
therefore a HARD dependency of this path -- do not "simplify" this script by
calling DuckDuckGo directly, it will not work.

stdlib only (urllib, re, json, argparse) -- no venv required, runs under any
Python interpreter on the machine.

CLI:
    python websearch.py "<query>" [--page N] [--region CODE] [--limit N]
                         [--json] [--timeout S] [--retries N]
    python websearch.py --queries-file PATH [same options]

Batch mode (--queries-file): PATH is UTF-8, one query per line (operators
intact); blank lines and lines starting with '#' are ignored. Exactly one of
the positional query / --queries-file must be given. Queries run
sequentially with the same --page/--region/--limit/--timeout/--retries.
Text output: one "=== QUERY <n>/<N>: <query> ===" header per query followed
by that query's normal text output, or "(no results)" / "(error: ...)".
--json output: a list of {"query": q, "exit": code, "results": [...]}
objects (failed queries also carry "error").

Exit codes:
    0 = at least one result returned (batch: by any query)
    3 = request succeeded but zero results parsed (batch: no query returned
        results and not every query failed on the network)
    4 = network/HTTP failure after retries (batch: every query failed)
    2 = bad usage (neither or both of query / --queries-file; unreadable or
        empty queries file)
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# NOTE: r.jina.ai sits behind Cloudflare, which challenges (403 "Just a
# moment...") requests carrying a browser-spoofed User-Agent (e.g. a Chrome
# UA string) without the rest of a real browser's header/TLS fingerprint.
# A plain non-browser UA (curl's default, or Python's own "Python-urllib/x.y")
# passes cleanly -- verified empirically 2026-09-19. So this deliberately
# does NOT send a Chrome/Firefox-style User-Agent; it lets urllib send its
# own default identifying UA string.
USER_AGENT = "Python-urllib/websearch.py (agent-reach)"

JINA_PREFIX = "https://r.jina.ai/"
DDG_BASE = "https://html.duckduckgo.com/html/"

RESULT_HEADING_RE = re.compile(
    r"^## \[(?P<title>.+?)\]\((?P<url>http[^)]+)\)", re.MULTILINE
)
SNIPPET_RE = re.compile(r"^\[(.{40,}?)\]\(http", re.MULTILINE)
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})T00:00:00")

SNIPPET_WINDOW = 2500


def _build_url(query, page=0, region=None):
    ddg_query = "q=" + urllib.parse.quote_plus(query)
    if page and page > 0:
        ddg_query += "&s=%d" % (page * 10)
    if region:
        ddg_query += "&kl=%s" % urllib.parse.quote_plus(region)
    ddg_url = DDG_BASE + "?" + ddg_query
    return JINA_PREFIX + ddg_url


def _unwrap_url(url):
    if "duckduckgo.com/l/" in url:
        parsed = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(parsed.query)
        if "uddg" in qs and qs["uddg"]:
            return urllib.parse.unquote(qs["uddg"][0])
    return url


def _extract_snippet(window_text):
    for m in SNIPPET_RE.finditer(window_text):
        candidate = m.group(1).strip()
        candidate_clean = candidate.replace("**", "")
        low = candidate_clean.lower()
        if "duckduckgo" in low:
            continue
        if candidate_clean.startswith("Image"):
            continue
        return candidate_clean[:200]
    return ""


def _extract_date(window_text):
    m = DATE_RE.search(window_text)
    if m:
        return m.group(1)
    return ""


def _fetch(url, timeout, retries):
    last_err = None
    delays = [2, 5]
    attempt = 0
    while attempt <= retries:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = getattr(resp, "status", resp.getcode())
                body = resp.read().decode("utf-8", errors="replace")
                if status >= 500 or status == 429:
                    raise urllib.error.HTTPError(url, status, "retryable", None, None)
                return body
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                last_err = e
            else:
                raise
        except Exception as e:  # network error, timeout, etc.
            last_err = e
        attempt += 1
        if attempt <= retries:
            time.sleep(delays[min(attempt - 1, len(delays) - 1)])
    raise RuntimeError("fetch failed after retries: %r" % (last_err,))


def search(query, page=0, region=None, limit=10, timeout=45, retries=2):
    url = _build_url(query, page=page, region=region)
    body = _fetch(url, timeout=timeout, retries=retries)

    results = []
    seen_urls = set()
    matches = list(RESULT_HEADING_RE.finditer(body))
    for i, m in enumerate(matches):
        title = m.group("title").strip()
        raw_url = m.group("url").strip()
        final_url = _unwrap_url(raw_url)
        # Sponsored/ad slots show up as duckduckgo.com/y.js?... (an ad-click
        # tracker, not the /l/?uddg= organic-redirect format _unwrap_url
        # handles) -- skip anything that still resolves inside
        # duckduckgo.com after unwrapping, it is not a real organic result.
        if "duckduckgo.com" in urllib.parse.urlparse(final_url).netloc:
            continue
        if final_url in seen_urls:
            continue

        window_start = m.end()
        window_end = min(len(body), window_start + SNIPPET_WINDOW)
        # don't bleed into the next heading's snippet window
        if i + 1 < len(matches):
            window_end = min(window_end, matches[i + 1].start())
        window_text = body[window_start:window_end]

        snippet = _extract_snippet(window_text)
        date = _extract_date(window_text)

        seen_urls.add(final_url)
        results.append(
            {
                "title": title,
                "url": final_url,
                "snippet": snippet,
                "date": date,
            }
        )

    return results[:limit]


def _print_results_text(results):
    for i, r in enumerate(results, 1):
        print("%d. %s" % (i, r["title"]))
        print("   %s" % r["url"])
        if r.get("date"):
            print("   DATE: %s" % r["date"])
        if r.get("snippet"):
            print("   SNIP: %s" % r["snippet"])
        print()


def read_queries_file(path):
    """One query per line; blank lines and '#' comment lines are skipped."""
    with open(path, encoding="utf-8-sig") as fh:
        lines = [ln.strip() for ln in fh.read().splitlines()]
    return [ln for ln in lines if ln and not ln.startswith("#")]


def batch_exit_code(codes):
    """0 if any query returned results, 4 if every query failed on the
    network, else 3 (no results anywhere)."""
    if any(c == 0 for c in codes):
        return 0
    if codes and all(c == 4 for c in codes):
        return 4
    return 3


def run_batch(queries, args):
    entries = []
    for q in queries:
        entry = {"query": q, "exit": 0, "results": []}
        try:
            entry["results"] = search(
                q,
                page=args.page,
                region=args.region,
                limit=args.limit,
                timeout=args.timeout,
                retries=args.retries,
            )
            if not entry["results"]:
                entry["exit"] = 3
        except Exception as e:
            entry["exit"] = 4
            entry["error"] = repr(e)
        entries.append(entry)

    if args.json:
        print(json.dumps(entries, ensure_ascii=False, indent=2))
    else:
        n = len(entries)
        for i, entry in enumerate(entries, 1):
            print("=== QUERY %d/%d: %s ===" % (i, n, entry["query"]))
            if entry["exit"] == 4:
                print("(error: %s)" % entry["error"])
                print()
            elif not entry["results"]:
                print("(no results)")
                print()
            else:
                _print_results_text(entry["results"])

    return batch_exit_code([e["exit"] for e in entries])


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(
        description="Free general-web search via Jina Reader + DuckDuckGo HTML."
    )
    parser.add_argument("query", nargs="?", default=None,
                        help="Search query (site:, -site:, OR, quotes all honoured)")
    parser.add_argument("--queries-file", default=None,
                        help="Batch mode: UTF-8 file, one query per line ('#' and blank lines ignored)")
    parser.add_argument("--page", type=int, default=0, help="0-indexed result page")
    parser.add_argument("--region", default=None, help="DDG region code, e.g. jp-jp, kr-kr")
    parser.add_argument("--limit", type=int, default=10, help="Max results to return")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    parser.add_argument("--timeout", type=float, default=45, help="Per-request timeout (s)")
    parser.add_argument("--retries", type=int, default=2, help="Retries on network/5xx/429")
    args = parser.parse_args(argv)

    if (args.query is None) == (args.queries_file is None):
        parser.error("give exactly one of: a query, or --queries-file PATH")

    if args.queries_file is not None:
        try:
            queries = read_queries_file(args.queries_file)
        except OSError as e:
            print("websearch.py: cannot read --queries-file: %r" % (e,), file=sys.stderr)
            return 2
        if not queries:
            print("websearch.py: --queries-file has no queries", file=sys.stderr)
            return 2
        return run_batch(queries, args)

    try:
        results = search(
            args.query,
            page=args.page,
            region=args.region,
            limit=args.limit,
            timeout=args.timeout,
            retries=args.retries,
        )
    except Exception as e:
        print("websearch.py: request failed: %r" % (e,), file=sys.stderr)
        return 4

    if not results:
        print("websearch.py: zero results parsed", file=sys.stderr)
        return 3

    if args.json:
        out = {
            "query": args.query,
            "page": args.page,
            "region": args.region,
            "count": len(results),
            "results": results,
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        _print_results_text(results)

    return 0


if __name__ == "__main__":
    sys.exit(main())
