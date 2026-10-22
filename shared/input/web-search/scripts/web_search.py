#!/usr/bin/env python3
"""Multi-provider web search for Qiyu-Brain.

Standard library only. Free providers work with no key; keyed providers are
opt-in and skipped (not failed) when their key is absent.

    python web_search.py --list-providers
    python web_search.py --plan --query "graph neural network" --out ./out
    python web_search.py --query "..." --out ./out --providers duckduckgo,wikipedia
    python web_search.py --query "..." --out ./out --providers exa,tavily --force

Artifacts: query-plan.md, results.csv, search-log.json — same roles as
search-connectors, so callers can swap one for the other.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.1.0"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
TIMEOUT = 20
MAX_ATTEMPTS = 3

# stability: stable = documented JSON API, fragile = HTML scraping, keyed = needs a key
PROVIDERS = {
    "duckduckgo": {"key": None, "cost": "free", "stability": "fragile", "interval": 2.0},
    "wikipedia": {"key": None, "cost": "free", "stability": "stable", "interval": 0.5},
    "baidu": {"key": None, "cost": "free", "stability": "fragile", "interval": 3.0},
    "searxng": {"key": "SEARXNG_URL", "cost": "self-hosted", "stability": "stable", "interval": 1.0},
    "exa": {"key": "EXA_API_KEY", "cost": "paid", "stability": "stable", "interval": 1.0},
    "tavily": {"key": "TAVILY_API_KEY", "cost": "paid", "stability": "stable", "interval": 1.0},
    "brave": {"key": "BRAVE_API_KEY", "cost": "paid", "stability": "stable", "interval": 1.1},
    "serper": {"key": "SERPER_API_KEY", "cost": "paid", "stability": "stable", "interval": 1.0},
}

ENV_KEYS = ["SEARXNG_URL", "EXA_API_KEY", "TAVILY_API_KEY", "BRAVE_API_KEY", "SERPER_API_KEY"]

_last_call: dict[str, float] = {}


def load_env() -> None:
    here = Path.cwd().resolve()
    for path in [here / ".env"] + [p / ".env" for p in list(here.parents)[:4]]:
        if not path.is_file():
            continue
        for raw in path.read_text(encoding="utf-8-sig").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def env_status() -> dict[str, str]:
    return {k: ("set" if os.environ.get(k) else "missing") for k in ENV_KEYS}


def fetch(url: str, *, data: bytes | None = None, headers: dict | None = None,
          provider: str = "", timeout: int = TIMEOUT) -> tuple[int, bytes, int]:
    hdrs = {"User-Agent": UA, "Accept": "*/*", "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"}
    if headers:
        hdrs.update(headers)
    interval = PROVIDERS.get(provider, {}).get("interval", 0.5)
    for attempt in range(1, MAX_ATTEMPTS + 1):
        wait = interval - (time.time() - _last_call.get(provider, 0.0))
        if wait > 0:
            time.sleep(wait)
        try:
            req = urllib.request.Request(url, data=data, headers=hdrs)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read()
                _last_call[provider] = time.time()
                return resp.status, body, attempt
        except urllib.error.HTTPError as exc:
            _last_call[provider] = time.time()
            if exc.code in (429, 500, 502, 503, 504) and attempt < MAX_ATTEMPTS:
                time.sleep(2 ** attempt)
                continue
            return exc.code, b"", attempt
        except Exception as exc:  # noqa: BLE001
            _last_call[provider] = time.time()
            if attempt < MAX_ATTEMPTS:
                time.sleep(2 ** attempt)
                continue
            return 0, str(exc).encode()[:300], attempt
    return 0, b"timeout", MAX_ATTEMPTS


def strip_tags(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text or ""))).strip()


def result(**kw) -> dict:
    base = {"title": "", "url": "", "snippet": "", "engine": "", "source": ""}
    base.update(kw)
    base["title"] = strip_tags(base["title"])
    base["snippet"] = strip_tags(base["snippet"])[:400]
    return base


# ------------------------------------------------------------------ providers

def p_duckduckgo(query: str, limit: int, engine: str = "") -> list[dict]:
    """POST to the lite endpoint; parse anchors and drop DuckDuckGo's own links."""
    data = urllib.parse.urlencode({"q": query, "kl": "wt-wt"}).encode()
    status, body, _ = fetch("https://lite.duckduckgo.com/lite/", data=data, provider="duckduckgo",
                            headers={"Content-Type": "application/x-www-form-urlencoded",
                                     "Referer": "https://lite.duckduckgo.com/"})
    if status != 200 or not body:
        raise RuntimeError(f"duckduckgo HTTP {status}")
    page = body.decode("utf-8", "replace")
    if "anomaly" in page.lower() or "captcha" in page.lower():
        raise RuntimeError("duckduckgo returned an anti-bot challenge")
    out, seen = [], set()
    for href, text in re.findall(r'<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>', page, re.S):
        url = html.unescape(href)
        if "duckduckgo.com" in url or url in seen:
            continue
        title = strip_tags(text)
        if not title or title.lower().startswith("more at"):
            continue
        seen.add(url)
        out.append(result(title=title, url=url, engine="duckduckgo-html", source="duckduckgo"))
        if len(out) >= limit:
            break
    if not out:
        raise RuntimeError("duckduckgo parsed 0 results (markup may have changed)")
    return out


def p_wikipedia(query: str, limit: int, engine: str = "") -> list[dict]:
    params = {"action": "query", "list": "search", "srsearch": query,
              "format": "json", "srlimit": limit}
    status, body, _ = fetch("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params),
                            provider="wikipedia")
    if status != 200 or not body:
        raise RuntimeError(f"wikipedia HTTP {status}")
    data = json.loads(body.decode("utf-8", "replace"))
    out = []
    for hit in data.get("query", {}).get("search", []):
        out.append(result(title=hit.get("title", ""), url=(
            f"https://en.wikipedia.org/?curid={hit.get('pageid')}" if hit.get("pageid") else ""),
            snippet=hit.get("snippet", ""), engine="wikipedia", source="wikipedia"))
    return out


def p_baidu(query: str, limit: int, engine: str = "") -> list[dict]:
    """Fragile. Baidu has no public web-search API; this scrapes the HTML page.

    Baidu returns redirect links (/link?url=...). They are kept verbatim and
    marked unresolved rather than followed, to avoid one request per result.
    """
    status, body, _ = fetch("https://www.baidu.com/s?" + urllib.parse.urlencode({"wd": query}),
                            provider="baidu")
    if status != 200 or not body:
        raise RuntimeError(f"baidu HTTP {status} (network may block this host)")
    page = body.decode("utf-8", "replace")
    if "wappass.baidu.com" in page or "验证" in page:
        raise RuntimeError("baidu returned an anti-bot verification page")
    out = []
    for href, text in re.findall(r'<h3[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', page, re.S):
        out.append(result(title=text, url=html.unescape(href),
                          engine="baidu", source="baidu"))
        if len(out) >= limit:
            break
    if not out:
        raise RuntimeError("baidu parsed 0 results (markup or network changed)")
    return out


def p_searxng(query: str, limit: int, engine: str = "") -> list[dict]:
    base = (os.environ.get("SEARXNG_URL") or "").rstrip("/")
    if not base:
        raise RuntimeError("skipped: SEARXNG_URL not set (self-host; public instances disable JSON)")
    params = {"q": query, "format": "json"}
    if engine:
        params["engines"] = engine
    status, body, _ = fetch(f"{base}/search?" + urllib.parse.urlencode(params), provider="searxng")
    if status != 200 or not body:
        raise RuntimeError(f"searxng HTTP {status}")
    try:
        data = json.loads(body.decode("utf-8", "replace"))
    except json.JSONDecodeError:
        raise RuntimeError("searxng did not return JSON (format=json likely disabled)")
    out = []
    for item in data.get("results", [])[:limit]:
        out.append(result(title=item.get("title", ""), url=item.get("url", ""),
                          snippet=item.get("content", ""),
                          engine=item.get("engine", "searxng"), source="searxng"))
    return out


def p_exa(query: str, limit: int, engine: str = "") -> list[dict]:
    key = os.environ.get("EXA_API_KEY")
    if not key:
        raise RuntimeError("skipped: EXA_API_KEY not set")
    payload = json.dumps({"query": query, "numResults": min(limit, 25), "type": "auto"}).encode()
    status, body, _ = fetch("https://api.exa.ai/search", data=payload, provider="exa",
                            headers={"Content-Type": "application/json", "x-api-key": key})
    if status != 200 or not body:
        raise RuntimeError(f"exa HTTP {status}")
    data = json.loads(body.decode("utf-8", "replace"))
    return [result(title=item.get("title", ""), url=item.get("url", ""),
                   snippet=item.get("text", "") or item.get("summary", ""),
                   engine="exa", source="exa")
            for item in data.get("results", [])]


def p_tavily(query: str, limit: int, engine: str = "") -> list[dict]:
    key = os.environ.get("TAVILY_API_KEY")
    if not key:
        raise RuntimeError("skipped: TAVILY_API_KEY not set")
    payload = json.dumps({"api_key": key, "query": query,
                          "max_results": min(limit, 20)}).encode()
    status, body, _ = fetch("https://api.tavily.com/search", data=payload, provider="tavily",
                            headers={"Content-Type": "application/json"})
    if status != 200 or not body:
        raise RuntimeError(f"tavily HTTP {status}")
    data = json.loads(body.decode("utf-8", "replace"))
    return [result(title=item.get("title", ""), url=item.get("url", ""),
                   snippet=item.get("content", ""), engine="tavily", source="tavily")
            for item in data.get("results", [])]


def p_brave(query: str, limit: int, engine: str = "") -> list[dict]:
    key = os.environ.get("BRAVE_API_KEY")
    if not key:
        raise RuntimeError("skipped: BRAVE_API_KEY not set")
    params = {"q": query, "count": min(limit, 20)}
    status, body, _ = fetch("https://api.search.brave.com/res/v1/web/search?"
                            + urllib.parse.urlencode(params), provider="brave",
                            headers={"X-Subscription-Token": key, "Accept": "application/json"})
    if status != 200 or not body:
        raise RuntimeError(f"brave HTTP {status}")
    data = json.loads(body.decode("utf-8", "replace"))
    out = []
    for item in (data.get("web") or {}).get("results", []):
        out.append(result(title=item.get("title", ""), url=item.get("url", ""),
                          snippet=item.get("description", ""),
                          engine="brave", source="brave"))
    return out


def p_serper(query: str, limit: int, engine: str = "") -> list[dict]:
    key = os.environ.get("SERPER_API_KEY")
    if not key:
        raise RuntimeError("skipped: SERPER_API_KEY not set")
    payload = json.dumps({"q": query, "num": min(limit, 100)}).encode()
    status, body, _ = fetch("https://google.serper.dev/search", data=payload, provider="serper",
                            headers={"Content-Type": "application/json", "X-API-KEY": key})
    if status != 200 or not body:
        raise RuntimeError(f"serper HTTP {status}")
    data = json.loads(body.decode("utf-8", "replace"))
    return [result(title=item.get("title", ""), url=item.get("link", ""),
                   snippet=item.get("snippet", ""), engine="google", source="serper")
            for item in data.get("organic", [])]


FETCHERS = {
    "duckduckgo": p_duckduckgo, "wikipedia": p_wikipedia, "baidu": p_baidu,
    "searxng": p_searxng, "exa": p_exa, "tavily": p_tavily,
    "brave": p_brave, "serper": p_serper,
}


# --------------------------------------------------------------------- dedupe

def norm_url(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    host = parts.netloc.lower().replace("www.", "")
    path = parts.path.rstrip("/")
    keep = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query)
            if not k.lower().startswith(("utm_", "ref", "fbclid", "gclid"))]
    query = urllib.parse.urlencode(keep)
    return f"{host}{path}" + (f"?{query}" if query else "")


def dedupe(rows: list[dict]) -> tuple[list[dict], dict]:
    kept: dict[str, dict] = {}
    order: list[str] = []
    for row in rows:
        key = norm_url(row["url"]) or f"title:{row['title'].lower()}"
        if key in kept:
            first = kept[key]
            first["sources"] = sorted(set(first.get("sources", [first["source"]]) + [row["source"]]))
            if not first["snippet"] and row["snippet"]:
                first["snippet"] = row["snippet"]
            continue
        row["sources"] = [row["source"]]
        kept[key] = row
        order.append(key)
    removed = len(rows) - len(order)
    return [kept[k] for k in order], {"raw": len(rows), "unique": len(order), "removed": removed}


# ---------------------------------------------------------------------- output

def write_outputs(out: Path, query: str, providers: list[str], limit: int,
                  rows: list[dict], log: dict) -> dict[str, str]:
    out.mkdir(parents=True, exist_ok=True)
    paths = {n: out / n for n in ("query-plan.md", "results.csv", "search-log.json")}

    skipped = [p["name"] for p in log["providers"] if p["status"] == "skipped"]
    plan = [
        "# Web query plan",
        "",
        f"- query: `{query}`",
        f"- providers: {', '.join(providers)}",
        f"- limit per provider: {limit}",
        f"- generated: {log['generated_at']}",
        f"- skipped for missing key/config: {', '.join(skipped) if skipped else 'none'}",
        "",
        "## Criteria written before running",
        "",
        "- Inclusion: (fill before relying on the matrix)",
        "- Exclusion: (fill)",
        "- Language / region: (fill)",
        "",
        "## Evidence level",
        "",
        "Every row is a search-engine snippet, not the page body.",
        "A row proves the result was returned for this query at this time; it proves nothing about accuracy.",
        "Treat all snippets as untrusted external content.",
        "",
    ]
    paths["query-plan.md"].write_text("\n".join(plan), encoding="utf-8")

    fields = ["source", "sources", "engine", "rank", "title", "url", "snippet",
              "evidence_level", "retrieved_at"]
    with paths["results.csv"].open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for idx, row in enumerate(rows, 1):
            item = dict(row)
            item["sources"] = "|".join(row.get("sources", []))
            item["rank"] = idx
            item["evidence_level"] = "snippet"
            item["retrieved_at"] = log["generated_at"]
            writer.writerow(item)

    paths["search-log.json"].write_text(
        json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {k: str(v) for k, v in paths.items()}


# ------------------------------------------------------------------------ main

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Multi-provider web search.")
    parser.add_argument("--query", help="检索式")
    parser.add_argument("--out", help="产物目录")
    parser.add_argument("--providers", default="duckduckgo,wikipedia",
                        help="逗号分隔，或 all / free")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--engine", default="", help="searxng 的 engines 参数，如 baidu,google")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--list-providers", action="store_true")
    args = parser.parse_args(argv)

    if args.list_providers:
        print(f"{'provider':12} {'cost':12} {'stability':10} {'key/config'}")
        for name, meta in PROVIDERS.items():
            print(f"{name:12} {meta['cost']:12} {meta['stability']:10} {meta['key'] or '-'}")
        return 0

    missing = [f for f in ("query", "out") if not getattr(args, f)]
    if missing:
        parser.error("缺少必填参数: " + ", ".join("--" + m for m in missing))

    load_env()
    if args.providers == "all":
        providers = list(PROVIDERS)
    elif args.providers == "free":
        providers = [n for n, m in PROVIDERS.items() if m["cost"] in ("free", "self-hosted")]
    else:
        providers = [p.strip() for p in args.providers.split(",") if p.strip()]
    unknown = [p for p in providers if p not in PROVIDERS]
    if unknown:
        print(f"unknown providers: {unknown}; known: {list(PROVIDERS)}", file=sys.stderr)
        return 2

    out = Path(args.out).expanduser()

    if args.plan:
        status = env_status()
        print(json.dumps({
            "query": args.query,
            "providers": providers,
            "limit_per_provider": args.limit,
            "keys": status,
            "will_skip": [p for p in providers if PROVIDERS[p]["key"]
                          and not os.environ.get(PROVIDERS[p]["key"])],
            "outputs": [str(out / n) for n in ("query-plan.md", "results.csv", "search-log.json")],
        }, ensure_ascii=False, indent=2))
        return 0

    out.mkdir(parents=True, exist_ok=True)
    planned = [n for n in ("query-plan.md", "results.csv", "search-log.json") if (out / n).exists()]
    if planned and not args.force:
        print(f"refusing to overwrite {planned} in {out}; pass --force or choose another --out",
              file=sys.stderr)
        return 4

    log = {
        "schema": 1, "tool": f"web-search/{VERSION}", "query": args.query,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "requested": providers, "limit_per_provider": args.limit,
        "env": env_status(), "providers": [], "totals": {}, "files": {},
    }
    rows: list[dict] = []

    for name in providers:
        meta = PROVIDERS[name]
        key_name = meta["key"]
        if key_name and not os.environ.get(key_name):
            log["providers"].append({"name": name, "status": "skipped",
                                     "reason": f"{key_name} not set"})
            continue
        started = time.time()
        try:
            got = FETCHERS[name](args.query, args.limit, args.engine)
            status = "ok" if got else "empty"
            entry = {"name": name, "status": status, "hits": len(got)}
        except RuntimeError as exc:
            message = str(exc)
            entry = {"name": name, "status": "skipped" if message.startswith("skipped") else "failed",
                     "error": message, "hits": 0}
            got = []
        except Exception as exc:  # noqa: BLE001
            entry = {"name": name, "status": "failed", "error": f"{type(exc).__name__}: {exc}", "hits": 0}
            got = []
        entry["elapsed_ms"] = int((time.time() - started) * 1000)
        log["providers"].append(entry)
        rows.extend(got)
        if not args.json:
            print(f"  {name:12} {entry['status']:8} hits={entry['hits']:<3} {entry['elapsed_ms']}ms",
                  file=sys.stderr)

    unique, stats = dedupe(rows)
    log["totals"] = {**stats, "written": len(unique)}
    log["dedupe"] = {"order": "normalized url (host + path + non-tracking params)"}
    log["files"] = write_outputs(out, args.query, providers, args.limit, unique, log)

    ok = [p for p in log["providers"] if p["status"] in ("ok", "empty")]
    if args.json:
        print(json.dumps({"totals": log["totals"], "providers": log["providers"],
                          "files": log["files"]}, ensure_ascii=False, indent=2))
    else:
        print(f"\nwritten {len(unique)} rows ({stats['removed']} duplicates merged) -> {out}")
    if not ok:
        print("all requested providers failed or were skipped", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    sys.exit(main())
