"""Live smoke verifier for websearch.py (stdlib only).

Run: python test_websearch.py

Exercises the real Jina Reader + DuckDuckGo path (no mocking) so a genuine
regression (Jina down, DDG markup change, unwrap broken) is caught. Each
case tolerates ONE retry to absorb transient network flake before failing.

The offline_* cases cover --queries-file batch mode with `search` monkeypatched
(no network): queries-file parsing, exit-code aggregation, JSON shape, and the
single-query text output staying unchanged.
"""

import contextlib
import io
import json
import os
import sys
import tempfile
import time

import websearch
from websearch import search


def _run_case(name, fn):
    for attempt in range(2):
        try:
            ok, detail = fn()
        except Exception as e:
            ok, detail = False, "exception: %r" % (e,)
        if ok:
            print("PASS: %s (%s)" % (name, detail))
            return True
        if attempt == 0:
            print("retry: %s failed once (%s), retrying..." % (name, detail))
            time.sleep(3)
    print("FAIL: %s (%s)" % (name, detail))
    return False


def case_english():
    results = search("best budget mechanical keyboard 2026", limit=10)
    if len(results) < 5:
        return False, "only %d results" % len(results)
    for r in results:
        if "duckduckgo.com/l/" in r["url"]:
            return False, "unwrap failed, saw raw ddg redirect: %s" % r["url"]
    return True, "%d results, no ddg redirects" % len(results)


def case_japanese():
    results = search("退職後の資産運用", region="jp-jp", limit=10)
    if len(results) < 5:
        return False, "only %d results" % len(results)
    return True, "%d results" % len(results)


def case_korean():
    results = search("은퇴 후 재테크", region="kr-kr", limit=10)
    if len(results) < 5:
        return False, "only %d results" % len(results)
    return True, "%d results" % len(results)


def case_reddit_operator():
    results = search("site:reddit.com retirement savings advice", limit=10)
    if len(results) < 5:
        return False, "only %d results" % len(results)
    for r in results:
        if "reddit.com" not in r["url"]:
            return False, "non-reddit url leaked through: %s" % r["url"]
    return True, "%d reddit results" % len(results)


def case_burst():
    queries = [
        "python asyncio tutorial",
        "best hiking boots 2026",
        "how to brew pour over coffee",
        "electric car battery degradation",
        "minimalist home office setup",
        "sourdough starter troubleshooting",
        "beginner guitar chords chart",
        "indoor plant care tips",
    ]
    start = time.time()
    all_ok = True
    for q in queries:
        results = search(q, limit=5)
        if len(results) < 1:
            all_ok = False
    elapsed = time.time() - start
    qpm = len(queries) / (elapsed / 60.0) if elapsed > 0 else float("inf")
    detail = "elapsed=%.1fs qpm=%.1f" % (elapsed, qpm)
    return all_ok, detail


@contextlib.contextmanager
def _fake_search(table):
    """table: query -> list of results | Exception instance."""
    real = websearch.search

    def fake(q, **kw):
        v = table[q]
        if isinstance(v, Exception):
            raise v
        return list(v)

    websearch.search = fake
    try:
        yield
    finally:
        websearch.search = real


def _run_main(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rc = websearch.main(argv)
        except SystemExit as e:
            rc = e.code
    return rc, out.getvalue(), err.getvalue()


def _queries_file(text):
    fd, path = tempfile.mkstemp(suffix=".txt", prefix=".tmp-websearch-test-")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


_R = [{"title": "T1", "url": "https://a.example/1", "snippet": "s1", "date": "2026-01-02"}]


def offline_queries_file_parsing():
    path = _queries_file('# batch 1\n\nsite:reddit.com "quoted q"\n  second -site:x.com  \n#skip\n')
    try:
        got = websearch.read_queries_file(path)
    finally:
        os.remove(path)
    want = ['site:reddit.com "quoted q"', "second -site:x.com"]
    return got == want, "parsed %r" % (got,)


def offline_exit_aggregation():
    agg = websearch.batch_exit_code
    checks = [([0, 3, 4], 0), ([3, 3], 3), ([4, 4], 4), ([3, 4], 3), ([0], 0)]
    bad = [(c, agg(c), w) for c, w in checks if agg(c) != w]
    return not bad, ("mismatches %r" % (bad,)) if bad else "5 combos ok"


def offline_batch_json_and_text():
    table = {"q one": _R, "q two": [], "q three": RuntimeError("boom")}
    path = _queries_file("q one\nq two\nq three\n")
    p2 = _queries_file("a\nb\n")
    try:
        with _fake_search(table):
            rc_j, out_j, _ = _run_main(["--queries-file", path, "--json", "--limit", "8"])
            rc_t, out_t, _ = _run_main(["--queries-file", path])
        with _fake_search({"a": [], "b": []}):
            rc_zero, _, _ = _run_main(["--queries-file", p2])
        with _fake_search({"a": RuntimeError("x"), "b": RuntimeError("y")}):
            rc_net, _, _ = _run_main(["--queries-file", p2])
    finally:
        os.remove(path)
        os.remove(p2)
    data = json.loads(out_j)
    ok = (
        rc_j == 0 and rc_t == 0 and rc_zero == 3 and rc_net == 4
        and [d["query"] for d in data] == ["q one", "q two", "q three"]
        and [d["exit"] for d in data] == [0, 3, 4]
        and data[0]["results"] == _R and data[1]["results"] == [] and "error" in data[2]
        and "=== QUERY 1/3: q one ===" in out_t
        and "=== QUERY 2/3: q two ===\n(no results)" in out_t
        and "=== QUERY 3/3: q three ===\n(error: " in out_t
        and "1. T1\n   https://a.example/1" in out_t
    )
    return ok, "rc json=%s text=%s zero=%s net=%s" % (rc_j, rc_t, rc_zero, rc_net)


def offline_single_query_unchanged():
    with _fake_search({"solo": _R}):
        rc, out, _ = _run_main(["solo"])
    want = "1. T1\n   https://a.example/1\n   DATE: 2026-01-02\n   SNIP: s1\n\n"
    rc_both, _, _ = _run_main(["solo", "--queries-file", "x.txt"])
    rc_none, _, _ = _run_main([])
    ok = rc == 0 and out == want and rc_both == 2 and rc_none == 2
    return ok, "rc=%s both=%s none=%s" % (rc, rc_both, rc_none)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    cases = [
        ("offline_queries_file_parsing", offline_queries_file_parsing),
        ("offline_exit_aggregation", offline_exit_aggregation),
        ("offline_batch_json_and_text", offline_batch_json_and_text),
        ("offline_single_query_unchanged", offline_single_query_unchanged),
        ("english", case_english),
        ("japanese", case_japanese),
        ("korean", case_korean),
        ("reddit_operator", case_reddit_operator),
        ("burst_8_queries", case_burst),
    ]

    all_pass = True
    for name, fn in cases:
        if not _run_case(name, fn):
            all_pass = False

    if all_pass:
        print("RESULT: PASS")
        return 0
    else:
        print("RESULT: FAIL")
        return 1


if __name__ == "__main__":
    sys.exit(main())
