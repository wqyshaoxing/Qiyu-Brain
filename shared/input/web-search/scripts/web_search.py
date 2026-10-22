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
    "duckduckgo": {"key": None, "cost": "free", "stability": "fragile", "interval": 2.0, "preset": "free"},
    "wikipedia": {"key": None, "cost": "free", "stability": "stable", "interval": 0.5, "preset": "free"},
    "hn": {"key": None, "cost": "free", "stability": "stable", "interval": 0.5, "preset": "free"},
    "stackexchange": {"key": None, "cost": "free", "stability": "stable", "interval": 0.5, "preset": "free"},
    "baidu": {"key": None, "cost": "free", "stability": "fragile", "interval": 3.0},
    "searxng": {"key": "SEARXNG_URL", "cost": "self-hosted", "stability": "stable", "interval": 1.0},
    "exa": {"key": "EXA_API_KEY", "cost": "paid", "stability": "stable", "interval": 1.0},
    "tavily": {"key": "TAVILY_API_KEY", "cost": "paid", "stability": "stable", "interval": 1.0},
    "brave": {"key": "BRAVE_API_KEY", "cost": "paid", "stability": "stable", "interval": 1.1},
    "jina": {"key": "JINA_API_KEY", "cost": "paid", "stability": "stable", "interval": 1.0},
    "firecrawl": {"key": "FIRECRAWL_API_KEY", "cost": "paid", "stability": "stable", "interval": 1.0},
    "linkup": {"key": "LINKUP_API_KEY", "cost": "paid", "stability": "stable", "interval": 1.0},
    "valyu": {"key": "VALYU_API_KEY", "cost": "paid", "stability": "stable", "interval": 1.0},
    "google_cse": {"key": "GOOGLE_CSE_KEY", "key2": "GOOGLE_CSE_CX",
                   "cost": "paid", "stability": "stable", "interval": 1.0},
    "bocha": {"key": "BOCHA_API_KEY", "cost": "paid", "stability": "unverified", "interval": 1.0},
    "langsearch": {"key": "LANGSEARCH_API_KEY", "cost": "paid", "stability": "unverified", "interval": 1.0},
}

ENV_KEYS = ["SEARXNG_URL", "EXA_API_KEY", "TAVILY_API_KEY", "BRAVE_API_KEY",
            "JINA_API_KEY", "FIRECRAWL_API_KEY", "LINKUP_API_KEY", "VALYU_API_KEY",
            "GOOGLE_CSE_KEY", "GOOGLE_CSE_CX", "BOCHA_API_KEY", "LANGSEARCH_API_KEY"]

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


def p_hn(query: str, limit: int, engine: str = "") -> list[dict]:
    """Hacker News via Algolia. No key; good for technical discussion, not facts."""
    params = {"query": query, "tags": "story", "hitsPerPage": min(limit, 30)}
    status, body, _ = fetch("https://hn.algolia.com/api/v1/search?" + urllib.parse.urlencode(params),
                            provider="hn")
    if status != 200 or not body:
        raise RuntimeError(f"hn HTTP {status}")
    data = json.loads(body.decode("utf-8", "replace"))
    out = []
    for hit in data.get("hits", []):
        oid = hit.get("objectID", "")
        out.append(result(
            title=hit.get("title") or "(untitled)",
            url=hit.get("url") or (f"https://news.ycombinator.com/item?id={oid}" if oid else ""),
            snippet=f"{hit.get('points', 0)} points, {hit.get('num_comments', 0)} comments",
            engine="hn-algolia", source="hn"))
    return out


def p_stackexchange(query: str, limit: int, engine: str = "") -> list[dict]:
    """StackExchange search; site defaults to stackoverflow, override with --engine."""
    site = engine or "stackoverflow"
    params = {"order": "desc", "sort": "relevance", "q": query,
              "site": site, "pagesize": min(limit, 30)}
    status, body, _ = fetch("https://api.stackexchange.com/2.3/search/advanced?"
                            + urllib.parse.urlencode(params), provider="stackexchange")
    if status != 200 or not body:
        raise RuntimeError(f"stackexchange HTTP {status}")
    data = json.loads(body.decode("utf-8", "replace"))
    out = []
    for item in data.get("items", []):
        out.append(result(title=item.get("title", ""), url=item.get("link", ""),
                          snippet=f"score {item.get('score', 0)}, "
                                  f"{'answered' if item.get('is_answered') else 'unanswered'}",
                          engine=site, source="stackexchange"))
    return out


def p_jina(query: str, limit: int, engine: str = "") -> list[dict]:
    key = os.environ.get("JINA_API_KEY")
    if not key:
        raise RuntimeError("skipped: JINA_API_KEY not set")
    status, body, _ = fetch("https://s.jina.ai/" + urllib.parse.quote(query), provider="jina",
                            headers={"Authorization": f"Bearer {key}", "Accept": "application/json"})
    if status != 200 or not body:
        raise RuntimeError(f"jina HTTP {status}")
    data = json.loads(body.decode("utf-8", "replace"))
    out = [result(title=r.get("title", ""), url=r.get("url", ""),
                  snippet=r.get("description") or r.get("content", ""),
                  engine="jina", source="jina")
           for r in (data.get("data") or [])]
    return out[:limit]


def p_firecrawl(query: str, limit: int, engine: str = "") -> list[dict]:
    key = os.environ.get("FIRECRAWL_API_KEY")
    if not key:
        raise RuntimeError("skipped: FIRECRAWL_API_KEY not set")
    payload = json.dumps({"query": query, "limit": min(limit, 10)}).encode()
    status, body, _ = fetch("https://api.firecrawl.dev/v1/search", data=payload, provider="firecrawl",
                            headers={"Content-Type": "application/json",
                                     "Authorization": f"Bearer {key}"})
    if status != 200 or not body:
        raise RuntimeError(f"firecrawl HTTP {status}")
    data = json.loads(body.decode("utf-8", "replace"))
    return [result(title=r.get("title", ""), url=r.get("url", ""),
                   snippet=r.get("description", ""), engine="firecrawl", source="firecrawl")
            for r in (data.get("data") or [])][:limit]


def p_linkup(query: str, limit: int, engine: str = "") -> list[dict]:
    key = os.environ.get("LINKUP_API_KEY")
    if not key:
        raise RuntimeError("skipped: LINKUP_API_KEY not set")
    payload = json.dumps({"q": query, "depth": "standard",
                          "outputType": "searchResults"}).encode()
    status, body, _ = fetch("https://api.linkup.so/v1/search", data=payload, provider="linkup",
                            headers={"Content-Type": "application/json",
                                     "Authorization": f"Bearer {key}"})
    if status != 200 or not body:
        raise RuntimeError(f"linkup HTTP {status}")
    data = json.loads(body.decode("utf-8", "replace"))
    return [result(title=r.get("name", ""), url=r.get("url", ""),
                   snippet=r.get("content", ""), engine="linkup", source="linkup")
            for r in (data.get("results") or [])][:limit]


def p_valyu(query: str, limit: int, engine: str = "") -> list[dict]:
    key = os.environ.get("VALYU_API_KEY")
    if not key:
        raise RuntimeError("skipped: VALYU_API_KEY not set")
    payload = json.dumps({"query": query, "max_num_results": min(limit, 10)}).encode()
    status, body, _ = fetch("https://api.valyu.ai/v1/search", data=payload, provider="valyu",
                            headers={"Content-Type": "application/json", "x-api-key": key})
    if status != 200 or not body:
        raise RuntimeError(f"valyu HTTP {status}")
    data = json.loads(body.decode("utf-8", "replace"))
    return [result(title=r.get("title", ""), url=r.get("url", ""),
                   snippet=r.get("content", ""), engine="valyu", source="valyu")
            for r in (data.get("results") or [])][:limit]


def p_google_cse(query: str, limit: int, engine: str = "") -> list[dict]:
    key = os.environ.get("GOOGLE_CSE_KEY")
    cx = os.environ.get("GOOGLE_CSE_CX")
    if not key or not cx:
        raise RuntimeError("skipped: GOOGLE_CSE_KEY / GOOGLE_CSE_CX not set")
    params = {"key": key, "cx": cx, "q": query, "num": min(limit, 10)}
    status, body, _ = fetch("https://www.googleapis.com/customsearch/v1?"
                            + urllib.parse.urlencode(params), provider="google_cse")
    if status != 200 or not body:
        raise RuntimeError(f"google_cse HTTP {status}")
    data = json.loads(body.decode("utf-8", "replace"))
    return [result(title=r.get("title", ""), url=r.get("link", ""),
                   snippet=r.get("snippet", ""), engine="google-cse", source="google_cse")
            for r in (data.get("items") or [])][:limit]


def _nested(obj, *path):
    for key in path:
        if not isinstance(obj, dict):
            return None
        obj = obj.get(key)
    return obj


def p_bocha(query: str, limit: int, engine: str = "") -> list[dict]:
    key = os.environ.get("BOCHA_API_KEY")
    if not key:
        raise RuntimeError("skipped: BOCHA_API_KEY not set")
    payload = json.dumps({"query": query, "count": min(limit, 10),
                          "summary": False}).encode()
    status, body, _ = fetch("https://api.bochaai.com/v1/web-search", data=payload, provider="bocha",
                            headers={"Content-Type": "application/json",
                                     "Authorization": f"Bearer {key}"})
    if status != 200 or not body:
        raise RuntimeError(f"bocha HTTP {status}")
    data = json.loads(body.decode("utf-8", "replace"))
    rows = (_nested(data, "data", "webPages", "value")
            or _nested(data, "webPages", "value") or [])
    if not rows:
        raise RuntimeError("bocha parsed 0 results; body: " + body[:200].decode("utf-8", "replace"))
    return [result(title=r.get("name", ""), url=r.get("url", ""),
                   snippet=r.get("snippet", ""), engine="bocha", source="bocha")
            for r in rows][:limit]


def p_langsearch(query: str, limit: int, engine: str = "") -> list[dict]:
    key = os.environ.get("LANGSEARCH_API_KEY")
    if not key:
        raise RuntimeError("skipped: LANGSEARCH_API_KEY not set")
    payload = json.dumps({"query": query, "count": min(limit, 10)}).encode()
    status, body, _ = fetch("https://api.langsearch.com/v1/web-search", data=payload,
                            provider="langsearch",
                            headers={"Content-Type": "application/json",
                                     "Authorization": f"Bearer {key}"})
    if status != 200 or not body:
        raise RuntimeError(f"langsearch HTTP {status}")
    data = json.loads(body.decode("utf-8", "replace"))
    rows = (_nested(data, "data", "webPages", "value")
            or _nested(data, "webPages", "value") or [])
    if not rows:
        raise RuntimeError("langsearch parsed 0 results; body: "
                           + body[:200].decode("utf-8", "replace"))
    return [result(title=r.get("name", ""), url=r.get("url", ""),
                   snippet=r.get("snippet", ""), engine="langsearch", source="langsearch")
            for r in rows][:limit]


FETCHERS = {
    "duckduckgo": p_duckduckgo, "wikipedia": p_wikipedia, "baidu": p_baidu,
    "hn": p_hn, "stackexchange": p_stackexchange,
    "searxng": p_searxng, "exa": p_exa, "tavily": p_tavily,
    "brave": p_brave, "jina": p_jina,
    "firecrawl": p_firecrawl, "linkup": p_linkup, "valyu": p_valyu,
    "google_cse": p_google_cse, "bocha": p_bocha,
    "langsearch": p_langsearch,
}


# --------------------------------------------------------------------- dedupe

NOISE_TITLES = {
    "waf page", "access denied", "access blocked", "just a moment...",
    "attention required!", "403 forbidden", "404 not found", "page not found",
    "are you a robot?", "verify you are human", "security check",
}


def is_noise(row: dict) -> bool:
    """Blocked or interstitial pages that search engines still index."""
    title = (row.get("title") or "").strip().lower()
    if title in NOISE_TITLES:
        return True
    return title.startswith(("waf ", "captcha", "error ")) or "access denied" in title


def norm_url(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    host = parts.netloc.lower().replace("www.", "")
    path = parts.path.rstrip("/")
    keep = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query)
            if not k.lower().startswith(("utm_", "ref", "fbclid", "gclid"))]
    query = urllib.parse.urlencode(keep)
    return f"{host}{path}" + (f"?{query}" if query else "")


def norm_title(text: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", (text or "").lower())


def dedupe(rows: list[dict]) -> tuple[list[dict], dict]:
    """Two passes: normalized URL, then identical normalized title.

    Regional mirrors (in./www./za./au. of the same article) share a title but
    not a URL, so a URL-only pass lets them through. The title pass merges them
    and keeps the alternate URLs for audit.
    """
    kept: dict[str, dict] = {}
    order: list[str] = []
    by_title: dict[str, str] = {}
    mirror_merges = 0

    for row in rows:
        key = norm_url(row["url"]) or f"title:{row['title'].lower()}"
        ntitle = norm_title(row["title"])

        if key in kept:
            first = kept[key]
            first["sources"] = sorted(set(first.get("sources", [first["source"]]) + [row["source"]]))
            if not first["snippet"] and row["snippet"]:
                first["snippet"] = row["snippet"]
            continue

        match_key = by_title.get(ntitle) if len(ntitle) >= 20 else None
        if match_key is None and len(ntitle) >= 30 and row["title"].rstrip().endswith(("...", "…")):
            # Engines truncate titles; a truncated title that prefixes a known one
            # is the same result, not a different page.
            for known_title, known_key in by_title.items():
                if len(known_title) >= 30 and (known_title.startswith(ntitle)
                                               or ntitle.startswith(known_title)):
                    match_key = known_key
                    break
        if match_key:
            first = kept[match_key]
            first.setdefault("alternate_urls", []).append(row["url"])
            first["sources"] = sorted(set(first.get("sources", [first["source"]]) + [row["source"]]))
            mirror_merges += 1
            continue

        row["sources"] = [row["source"]]
        kept[key] = row
        order.append(key)
        if len(ntitle) >= 20:
            by_title[ntitle] = key

    removed = len(rows) - len(order)
    return [kept[k] for k in order], {"raw": len(rows), "unique": len(order),
                                      "removed": removed, "mirrors_merged": mirror_merges}


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

    fields = ["source", "sources", "engine", "rank", "title", "url", "alt_urls",
              "snippet", "evidence_level", "retrieved_at"]
    with paths["results.csv"].open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for idx, row in enumerate(rows, 1):
            item = dict(row)
            item["sources"] = "|".join(row.get("sources", []))
            item["alt_urls"] = "|".join(row.get("alternate_urls", []))
            item["rank"] = idx
            item["evidence_level"] = "snippet"
            item["retrieved_at"] = log["generated_at"]
            writer.writerow(item)

    log["files"] = {k: str(v) for k, v in paths.items()}
    paths["search-log.json"].write_text(
        json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return log["files"]


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
    parser.add_argument("--doctor", action="store_true",
                        help="逐个来源实测：缺 key / 失败 / 可用，附原始错误片段")
    args = parser.parse_args(argv)

    if args.list_providers:
        print(f"{'provider':14} {'cost':12} {'stability':10} {'key/config'}")
        for name, meta in PROVIDERS.items():
            print(f"{name:14} {meta['cost']:12} {meta['stability']:10} {meta['key'] or '-'}")
        return 0

    if args.doctor:
        load_env()
        print(f"{'provider':14} {'key':26} {'status':8} detail")
        for name, meta in PROVIDERS.items():
            keys = [k for k in (meta["key"], meta.get("key2")) if k]
            label = ",".join(keys) or "-"
            missing = [k for k in keys if not os.environ.get(k)]
            if missing:
                print(f"{name:14} {label:26} {'missing':8} {', '.join(missing)}")
                continue
            try:
                got = FETCHERS[name]("agent skills", 1, "")
                print(f"{name:14} {label:26} {'ok':8} {len(got)} 条")
            except RuntimeError as exc:
                msg = str(exc)
                status = "skip" if msg.startswith("skipped") else "fail"
                print(f"{name:14} {label:26} {status:8} {msg[:90]}")
            except Exception as exc:  # noqa: BLE001
                print(f"{name:14} {label:26} {'fail':8} {type(exc).__name__}: {str(exc)[:70]}")
        return 0

    missing = [f for f in ("query", "out") if not getattr(args, f)]
    if missing:
        parser.error("缺少必填参数: " + ", ".join("--" + m for m in missing))

    load_env()
    if args.providers == "all":
        providers = list(PROVIDERS)
    elif args.providers == "free":
        providers = [n for n, m in PROVIDERS.items() if m.get("preset") == "free"]
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
            "will_skip": [p for p in providers
                          if any(k and not os.environ.get(k)
                                 for k in (PROVIDERS[p]["key"],
                                           PROVIDERS[p].get("key2")))],
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
        required = [k for k in (meta["key"], meta.get("key2")) if k]
        missing_keys = [k for k in required if not os.environ.get(k)]
        if missing_keys:
            log["providers"].append({"name": name, "status": "skipped",
                                     "reason": ", ".join(missing_keys) + " not set"})
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
        noisy = [r for r in got if is_noise(r)]
        if noisy:
            got = [r for r in got if not is_noise(r)]
            entry["filtered_noise"] = len(noisy)
            entry["hits"] = len(got)
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
