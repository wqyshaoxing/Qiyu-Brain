#!/usr/bin/env python3
"""Bounded multi-source scholarly search for Qiyu-Brain.

Standard library only, so an installed skill needs no dependency step.

    python search.py --plan --query "graph neural network" --out ./out
    python search.py --query "graph neural network" --out ./out --limit 10
    python search.py --query "..." --out ./out --providers arxiv,openalex --force

Writes three artifacts: query-plan.md, results.csv, search-log.json.
Never downloads full texts; every row is metadata-level evidence.
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
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.1.0"
UA = f"Qiyu-Brain/{VERSION} (+https://github.com/wqyshaoxing/Qiyu-Brain)"
TIMEOUT = 25
MAX_ATTEMPTS = 3

PROVIDERS = {
    "arxiv": {"key": None, "interval": 3.0, "cost": "free"},
    "crossref": {"key": None, "interval": 1.0, "cost": "free"},
    "openalex": {"key": None, "interval": 0.2, "cost": "free"},
    "pubmed": {"key": "PUBMED_API_KEY", "interval": 0.4, "cost": "free"},
    "semantic_scholar": {"key": None, "interval": 1.2, "cost": "free", "retry_429": False},
    "exa": {"key": "EXA_API_KEY", "interval": 1.0, "cost": "paid"},
}

ENV_KEYS = ["CROSSREF_MAILTO", "SEMANTIC_SCHOLAR_API_KEY", "PUBMED_API_KEY",
            "EXA_API_KEY", "ZOTERO_API_KEY", "ZOTERO_LIBRARY_ID", "MINERU_API_KEY"]

_last_call: dict[str, float] = {}


# ---------------------------------------------------------------- environment

def load_env() -> None:
    """Read every config file found; real environment variables always win.

    Order: QIYU_ENV_FILE, then .env from cwd up to 4 parents, then
    ~/.dsh/qiyu.env — the last one is what lets an installed skill (living
    under a host skills root, far from the repo) still see its keys.
    """
    here = Path.cwd().resolve()
    candidates = [p / ".env" for p in [here] + list(here.parents)[:4]]
    explicit = os.environ.get("QIYU_ENV_FILE")
    if explicit:
        candidates.insert(0, Path(explicit).expanduser())
    dsh_home = Path(os.environ.get("DSH_HOME") or (Path.home() / ".dsh"))
    candidates.append(dsh_home / "qiyu.env")
    for path in candidates:
        if not path.is_file():
            continue
        for raw in path.read_text(encoding="utf-8-sig").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def env_status() -> dict[str, str]:
    return {k: ("set" if os.environ.get(k) else "missing") for k in ENV_KEYS}


# -------------------------------------------------------------------- network

def fetch(url: str, *, data: bytes | None = None, headers: dict | None = None,
          provider: str = "") -> tuple[int, bytes, int]:
    """GET/POST with bounded exponential backoff. Returns (status, body, attempts)."""
    hdrs = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        hdrs.update(headers)
    interval = PROVIDERS.get(provider, {}).get("interval", 0.5)
    last_error: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        wait = interval - (time.time() - _last_call.get(provider, 0.0))
        if wait > 0:
            time.sleep(wait)
        try:
            req = urllib.request.Request(url, data=data, headers=hdrs)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                body = resp.read()
                _last_call[provider] = time.time()
                return resp.status, body, attempt
        except urllib.error.HTTPError as exc:
            _last_call[provider] = time.time()
            retryable = (exc.code != 429) or PROVIDERS.get(provider, {}).get("retry_429", True)
            if exc.code in (429, 500, 502, 503, 504) and attempt < MAX_ATTEMPTS and retryable:
                time.sleep(2 ** attempt)
                last_error = exc
                continue
            return exc.code, b"", attempt
        except Exception as exc:  # noqa: BLE001 - network layer must not crash the run
            last_error = exc
            _last_call[provider] = time.time()
            if attempt < MAX_ATTEMPTS:
                time.sleep(2 ** attempt)
                continue
            return 0, str(exc).encode()[:300], attempt
    return 0, str(last_error).encode()[:300] if last_error else b"", MAX_ATTEMPTS


def as_json(body: bytes) -> dict:
    return json.loads(body.decode("utf-8", "replace"))


def clean(text: str | None) -> str:
    if not text:
        return ""
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    return re.sub(r"\s+", " ", text).strip()


def record(**kw) -> dict:
    base = {"title": "", "authors": "", "year": "", "venue": "", "doi": "",
            "arxiv_id": "", "url": "", "source": "", "source_id": ""}
    base.update(kw)
    for k in ("title", "authors", "venue", "doi", "url"):
        base[k] = clean(str(base[k]))
    return base


# ------------------------------------------------------------------ providers

def p_arxiv(query: str, limit: int) -> list[dict]:
    term = f'all:"{query}"' if " " in query else f"all:{query}"
    q = urllib.parse.quote(term)
    url = f"https://export.arxiv.org/api/query?search_query={q}&start=0&max_results={limit}"
    status, body, _ = fetch(url, provider="arxiv")
    if status != 200 or not body:
        raise RuntimeError(f"arxiv HTTP {status}")
    ns = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    out = []
    for entry in ET.fromstring(body).findall("a:entry", ns):
        aid = clean((entry.findtext("a:id", "", ns) or "").rsplit("/", 1)[-1])
        out.append(record(
            title=clean(entry.findtext("a:title", "", ns)),
            authors=", ".join(clean(a.findtext("a:name", "", ns))
                             for a in entry.findall("a:author", ns)),
            year=clean((entry.findtext("a:published", "", ns) or "")[:4]),
            venue="arXiv",
            doi=clean(entry.findtext("arxiv:doi", "", ns)),
            arxiv_id=aid,
            url=f"https://arxiv.org/abs/{aid}" if aid else "",
            source="arxiv",
            source_id=aid,
        ))
    return out


def p_crossref(query: str, limit: int) -> list[dict]:
    params = {"query.bibliographic": query, "rows": limit,
              "select": "DOI,title,author,issued,container-title,URL,type"}
    mailto = os.environ.get("CROSSREF_MAILTO")
    if mailto:
        params["mailto"] = mailto
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    status, body, _ = fetch(url, provider="crossref")
    if status != 200 or not body:
        raise RuntimeError(f"crossref HTTP {status}")
    out = []
    for item in as_json(body).get("message", {}).get("items", []):
        year = ""
        for field in ("issued", "published-print", "published-online"):
            parts = (item.get(field) or {}).get("date-parts") or [[]]
            if parts and parts[0] and parts[0][0]:
                year = str(parts[0][0])
                break
        out.append(record(
            title=(item.get("title") or [""])[0],
            authors=", ".join(
                f"{a.get('family', '')} {a.get('given', '')}".strip()
                for a in (item.get("author") or [])),
            year=year,
            venue=(item.get("container-title") or [""])[0],
            doi=item.get("DOI", ""),
            url=item.get("URL", ""),
            source="crossref",
            source_id=item.get("DOI", ""),
        ))
    return out


def p_openalex(query: str, limit: int) -> list[dict]:
    url = ("https://api.openalex.org/works?"
           + urllib.parse.urlencode({"search": query, "per-page": limit}))
    status, body, _ = fetch(url, provider="openalex")
    if status != 200 or not body:
        raise RuntimeError(f"openalex HTTP {status}")
    out = []
    for item in as_json(body).get("results", []):
        doi = (item.get("doi") or "").replace("https://doi.org/", "")
        loc = item.get("primary_location") or {}
        src = (loc.get("source") or {})
        out.append(record(
            title=item.get("display_name", ""),
            authors=", ".join(
                (a.get("author") or {}).get("display_name", "")
                for a in (item.get("authorships") or [])),
            year=item.get("publication_year", ""),
            venue=src.get("display_name", ""),
            doi=doi,
            url=item.get("id", ""),
            source="openalex",
            source_id=(item.get("id") or "").rsplit("/", 1)[-1],
        ))
    return out


def p_pubmed(query: str, limit: int) -> list[dict]:
    key = os.environ.get("PUBMED_API_KEY", "")
    params = {"db": "pubmed", "term": query, "retmax": limit, "retmode": "json"}
    if key:
        params["api_key"] = key
    s1 = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urllib.parse.urlencode(params)
    status, body, _ = fetch(s1, provider="pubmed")
    if status != 200 or not body:
        raise RuntimeError(f"pubmed esearch HTTP {status}")
    ids = as_json(body).get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []
    params2 = {"db": "pubmed", "id": ",".join(ids), "retmode": "xml"}
    if key:
        params2["api_key"] = key
    s2 = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + urllib.parse.urlencode(params2)
    status, body, _ = fetch(s2, provider="pubmed")
    if status != 200 or not body:
        raise RuntimeError(f"pubmed efetch HTTP {status}")
    out = []
    for art in ET.fromstring(body).findall(".//PubmedArticle"):
        doi, pmid = "", ""
        for aid in art.findall(".//ArticleId"):
            if aid.get("IdType") == "doi":
                doi = clean(aid.text)
            elif aid.get("IdType") == "pubmed":
                pmid = clean(aid.text)
        out.append(record(
            title=clean(art.findtext(".//ArticleTitle", "")),
            authors=", ".join(
                f"{clean(a.findtext('LastName', ''))} {clean(a.findtext('ForeName', ''))}".strip()
                for a in art.findall(".//Author")),
            year=clean(art.findtext(".//PubDate/Year", "") or art.findtext(".//ArticleDate/Year", "")),
            venue=clean(art.findtext(".//Journal/Title", "")),
            doi=doi,
            url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
            source="pubmed",
            source_id=pmid,
        ))
    return out


def p_semantic_scholar(query: str, limit: int) -> list[dict]:
    """Anonymous access works; a key only raises the rate limit."""
    key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    params = {"query": query, "limit": min(limit, 100),
              "fields": "title,authors,year,venue,externalIds,url"}
    url = "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode(params)
    headers = {"x-api-key": key} if key else {}
    status, body, _ = fetch(url, provider="semantic_scholar", headers=headers)
    if status == 429:
        raise RuntimeError(
            "semantic_scholar HTTP 429: anonymous rate limit (shared pool is saturated; "
            "measured 3/3 attempts). A key is required for stable use and is intentionally "
            "not configured. Use arxiv / crossref / openalex instead."
        )
    if status != 200 or not body:
        raise RuntimeError(f"semantic_scholar HTTP {status}")
    out = []
    for item in as_json(body).get("data", []):
        ext = item.get("externalIds") or {}
        out.append(record(
            title=item.get("title", ""),
            authors=", ".join(a.get("name", "") for a in (item.get("authors") or [])),
            year=item.get("year", ""),
            venue=item.get("venue", ""),
            doi=ext.get("DOI", ""),
            arxiv_id=ext.get("ArXiv", ""),
            url=item.get("url", ""),
            source="semantic_scholar",
            source_id=item.get("paperId", ""),
        ))
    return out


def p_exa(query: str, limit: int) -> list[dict]:
    key = os.environ.get("EXA_API_KEY")
    if not key:
        raise RuntimeError("skipped: EXA_API_KEY not set")
    payload = json.dumps({"query": query, "numResults": min(limit, 25),
                          "type": "auto"}).encode()
    status, body, _ = fetch("https://api.exa.ai/search", data=payload, provider="exa",
                            headers={"Content-Type": "application/json", "x-api-key": key})
    if status != 200 or not body:
        raise RuntimeError(f"exa HTTP {status}")
    out = []
    for item in as_json(body).get("results", []):
        out.append(record(
            title=item.get("title", ""),
            authors=", ".join(item.get("author") or []),
            year=(item.get("publishedDate") or "")[:4],
            venue="web",
            url=item.get("url", ""),
            source="exa",
            source_id=item.get("id", ""),
        ))
    return out


FETCHERS = {
    "arxiv": p_arxiv, "crossref": p_crossref, "openalex": p_openalex,
    "pubmed": p_pubmed, "semantic_scholar": p_semantic_scholar, "exa": p_exa,
}


# --------------------------------------------------------------------- dedupe

def norm_title(text: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", text.lower())


def dedupe(rows: list[dict]) -> tuple[list[dict], dict]:
    kept: dict[str, dict] = {}
    order: list[str] = []
    collisions: list[dict] = []
    for row in rows:
        doi = row["doi"].lower()
        if doi:
            key = f"doi:{doi}"
        elif row["arxiv_id"]:
            key = f"arxiv:{row['arxiv_id'].lower()}"
        elif norm_title(row["title"]):
            key = f"title:{norm_title(row['title'])}:{row['year']}"
        else:
            key = f"anon:{row['source']}:{row['source_id']}"
        if key in kept:
            first = kept[key]
            first["sources"] = sorted(set(first.get("sources", [first["source"]]) + [row["source"]]))
            for field in ("doi", "arxiv_id", "url", "year", "venue", "authors"):
                if not first[field] and row[field]:
                    first[field] = row[field]
            collisions.append({"key": key, "kept": first["title"], "duplicate_source": row["source"]})
            continue
        row["sources"] = [row["source"]]
        kept[key] = row
        order.append(key)
    stats = {"raw": len(rows), "unique": len(order), "removed": len(rows) - len(order),
             "collisions": collisions[:20]}
    return [kept[k] for k in order], stats


# ---------------------------------------------------------------------- output

def write_outputs(out: Path, query: str, providers: list[str], limit: int,
                  rows: list[dict], log: dict, force: bool) -> dict[str, str]:
    out.mkdir(parents=True, exist_ok=True)
    paths = {name: out / name for name in ("query-plan.md", "results.csv", "search-log.json")}
    existing = [p.name for p in paths.values() if p.exists()]
    if existing and not force:
        raise SystemExit(f"refusing to overwrite {existing}; pass --force or choose another --out")

    plan = [
        "# Query plan",
        "",
        f"- query: `{query}`",
        f"- providers: {', '.join(providers)}",
        f"- limit per provider: {limit}",
        f"- generated: {log['generated_at']}",
        "",
        "## Criteria written before running",
        "",
        "- Inclusion: (fill before relying on the matrix)",
        "- Exclusion: (fill before relying on the matrix)",
        "- Date range: (fill)",
        "",
        "## Evidence level",
        "",
        "Every row is metadata only. Abstracts are not read, full texts are not fetched.",
        "A row proves the record exists and is retrievable from the named source at the given time.",
        "",
        "## Provenance",
        "",
        "See `search-log.json` for per-provider status, retries, failures, and dedup counts.",
        "",
    ]
    paths["query-plan.md"].write_text("\n".join(plan), encoding="utf-8")

    fields = ["source", "sources", "source_id", "doi", "arxiv_id", "title",
              "authors", "year", "venue", "url", "evidence_level", "retrieved_at"]
    with paths["results.csv"].open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            item = dict(row)
            item["sources"] = "|".join(row.get("sources", []))
            item["evidence_level"] = "metadata"
            item["retrieved_at"] = log["generated_at"]
            writer.writerow(item)

    log["files"] = {k: str(v) for k, v in paths.items()}
    paths["search-log.json"].write_text(
        json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return log["files"]


def build_log(query: str, providers: list[str], limit: int) -> dict:
    return {
        "schema": 1,
        "tool": f"shared-scholarly-search/{VERSION}",
        "query": query,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "requested": providers,
        "limit_per_provider": limit,
        "env": env_status(),
        "providers": [],
        "totals": {},
        "files": {},
    }


# ------------------------------------------------------------------------ main

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bounded multi-source scholarly search.")
    parser.add_argument("--query", help="检索式")
    parser.add_argument("--out", help="产物目录")
    parser.add_argument("--providers", default="arxiv,crossref,openalex",
                        help="逗号分隔，或 all")
    parser.add_argument("--limit", type=int, default=20, help="每个来源的条数上限")
    parser.add_argument("--plan", action="store_true", help="只打印计划，不联网")
    parser.add_argument("--force", action="store_true", help="允许覆盖已有产物")
    parser.add_argument("--json", action="store_true", help="以 JSON 打印运行摘要")
    parser.add_argument("--list-providers", action="store_true")
    args = parser.parse_args(argv)

    if args.list_providers:
        for name, meta in PROVIDERS.items():
            key = meta["key"] or "-"
            print(f"{name:18} cost={meta['cost']:16} interval={meta['interval']}s key={key}")
        return 0

    missing = [flag for flag in ("query", "out") if not getattr(args, flag)]
    if missing:
        parser.error("缺少必填参数: " + ", ".join("--" + m for m in missing))

    load_env()
    providers = list(PROVIDERS) if args.providers == "all" else [
        p.strip() for p in args.providers.split(",") if p.strip()]
    unknown = [p for p in providers if p not in PROVIDERS]
    if unknown:
        print(f"unknown providers: {unknown}; known: {list(PROVIDERS)}", file=sys.stderr)
        return 2

    out = Path(args.out).expanduser()

    if args.plan:
        status = env_status()
        plan = {
            "query": args.query,
            "providers": providers,
            "limit_per_provider": args.limit,
            "keys": {p: (PROVIDERS[p]["key"] and status.get(PROVIDERS[p]["key"], "missing")) for p in providers},
            "will_skip": [p for p in providers
                          if PROVIDERS[p]["key"] and not os.environ.get(PROVIDERS[p]["key"])],
            "outputs": [str(out / n) for n in ("query-plan.md", "results.csv", "search-log.json")],
            "network_requests": f"<= {len(providers) * 2} (pubmed uses 2 calls)",
        }
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0

    log = build_log(args.query, providers, args.limit)
    rows: list[dict] = []

    out.mkdir(parents=True, exist_ok=True)
    planned = [n for n in ("query-plan.md", "results.csv", "search-log.json") if (out / n).exists()]
    if planned and not args.force:
        print(f"refusing to overwrite {planned} in {out}; pass --force or choose another --out",
              file=sys.stderr)
        return 4

    for name in providers:
        meta = PROVIDERS[name]
        key_name = meta["key"]
        if key_name and not os.environ.get(key_name):
            log["providers"].append({"name": name, "status": "skipped",
                                     "reason": f"{key_name} not set"})
            continue
        started = time.time()
        try:
            got = FETCHERS[name](args.query, args.limit)
            row = {"name": name, "status": "ok", "hits": len(got)}
        except RuntimeError as exc:
            message = str(exc)
            row = {"name": name, "status": "skipped" if message.startswith("skipped") else "failed",
                   "error": message, "hits": 0}
            got = []
        except Exception as exc:  # noqa: BLE001
            row = {"name": name, "status": "failed", "error": f"{type(exc).__name__}: {exc}", "hits": 0}
            got = []
        row["elapsed_ms"] = int((time.time() - started) * 1000)
        log["providers"].append(row)
        rows.extend(got)
        if not args.json:
            print(f"  {name:18} {row['status']:8} hits={row['hits']:<3} {row['elapsed_ms']}ms",
                  file=sys.stderr)

    unique, stats = dedupe(rows)
    log["totals"] = {"raw": stats["raw"], "unique": stats["unique"],
                     "removed": stats["removed"], "written": len(unique)}
    log["dedupe"] = {"order": "doi > arxiv_id > normalized title+year",
                     "collisions_sample": stats["collisions"]}
    log["files"] = write_outputs(out, args.query, providers, args.limit, unique, log, args.force)

    ok_any = any(p["status"] == "ok" for p in log["providers"])
    if args.json:
        print(json.dumps({"totals": log["totals"], "providers": log["providers"],
                          "files": log["files"]}, ensure_ascii=False, indent=2))
    else:
        print(f"\nwritten {len(unique)} rows ({stats['removed']} duplicates merged) -> {out}")
    if not ok_any:
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
