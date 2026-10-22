#!/usr/bin/env python3
"""Build installable plugin bundles from the Qiyu-Brain source tree.

Source layout is domain/stage/skill; hosts want a flat skills/<name>/ layout.
This script flattens, copies each skill self-contained, and writes a manifest.

    python scripts/build_plugin.py                     # build default hosts
    python scripts/build_plugin.py --hosts generic,agents
    python scripts/build_plugin.py --check             # verify dist/ instead
    python scripts/build_plugin.py --hosts claude --out dist

Design notes:
- Bundles are self-contained: each skill keeps SKILL.md, runtime.json,
  references/ and scripts/. Hosts never reach back into the repo.
- A skill's scripts are imported by path, never across skills, so vendoring
  is a straight copy. If shared/_lib exists it is copied to <skill>/_runtime/.
- Build refuses to ship anything that looks like a secret, and never copies
  .env, dist/, search-out/ or .git/.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.1.0"
PLUGIN_NAME = "qiyu-brain"
RESERVED = {"scripts", "docs", "_core", "_memory", "_eval", "_profile",
            "third-party", "search-out", "dist", "config"}
STAGES = ("input", "reasoning", "output", "verify")

# host -> layout. verified means the layout was tested against a real host;
# assumed means it follows a documented convention but is untested here.
HOSTS = {
    "generic": {"skills_dir": "skills", "layout": "verified"},
    "agents": {"skills_dir": ".agents/skills", "layout": "verified"},
    "claude": {"skills_dir": "skills", "plugin": ".claude-plugin/plugin.json",
               "layout": "assumed"},
    # A real cordis plugin: package.json + lib/index.js + bundled skills/.
    # Installed through the host's plugin manager or by copying into a profile.
    "dsh-plugin": {"skills_dir": "skills", "layout": "verified",
                   "plugin_src": "plugin"},
}

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"tvly-[A-Za-z0-9_\-]{10,}"),
    re.compile(r"fc-[A-Za-z0-9_\-]{10,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{30,}"),
]
SKIP_DIRS = {".git", "__pycache__", "dist", "search-out", "_dsh-extract"}


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    data: dict = {}
    for line in text[3:end].splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line or line.startswith((" ", "\t")):
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key.strip()] = [v.strip() for v in inner.split(",") if v.strip()] if inner else []
        else:
            data[key.strip()] = value.strip("'\"")
    return data


def discover_skills(root: Path) -> list[dict]:
    found: list[dict] = []
    for part in sorted(root.iterdir()):
        if not part.is_dir() or part.name in RESERVED or part.name.startswith((".", "_")):
            continue
        children = [c for c in sorted(part.iterdir()) if c.is_dir() and not c.name.startswith(".")]
        flat = any((c / "SKILL.md").is_file() for c in children)
        if flat:
            for skill in children:
                if (skill / "SKILL.md").is_file():
                    found.append(_describe(skill, part.name))
        else:
            for stage in children:
                if stage.name not in STAGES:
                    continue
                for skill in sorted(stage.iterdir()):
                    if skill.is_dir() and (skill / "SKILL.md").is_file():
                        found.append(_describe(skill, part.name))
    return found


def _describe(skill: Path, partition: str) -> dict:
    meta = parse_frontmatter((skill / "SKILL.md").read_text(encoding="utf-8"))
    runtime: dict = {}
    rt = skill / "runtime.json"
    if rt.is_file():
        try:
            runtime = json.loads(rt.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            runtime = {}
    actions = [a for a in runtime.get("actions", []) if isinstance(a, dict)]
    parameters = next((a.get("parameters") for a in actions
                       if isinstance(a.get("parameters"), dict)), None)
    return {
        "name": meta.get("name") or skill.name,
        "partition": partition,
        "stage": meta.get("stage") or [],
        "source": skill,
        "actions": [a.get("script") for a in actions if a.get("script")],
        "optional_requires": sorted({k for a in actions for k in a.get("optional_requires", [])}),
        "artifacts": [a.get("role") for a in runtime.get("artifacts", []) if isinstance(a, dict)],
        "parameters": parameters,
    }


def copy_skill(skill: dict, dest_root: Path) -> Path:
    dest = dest_root / skill["name"]
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(skill["source"], dest,
                    ignore=shutil.ignore_patterns(*SKIP_DIRS, ".env", "*.pyc"))
    lib = skill["source"].parents[0] / "_lib"  # optional shared helpers
    if lib.is_dir():
        shutil.copytree(lib, dest / "_runtime" / "_lib",
                        ignore=shutil.ignore_patterns(*SKIP_DIRS))
    return dest


def git_commit(root: Path) -> str:
    try:
        out = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:  # noqa: BLE001
        return ""


def scan_secrets(path: Path) -> list[str]:
    hits: list[str] = []
    for file in path.rglob("*"):
        if not file.is_file() or file.suffix in {".png", ".jpg", ".zip"}:
            continue
        if file.name == ".env.example":
            continue
        try:
            text = file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in SECRET_PATTERNS:
            for m in pattern.finditer(text):
                hits.append(f"{file.relative_to(path)}: {m.group(0)[:12]}…")
    return hits


def build(root: Path, out: Path, hosts: list[str], version: str) -> int:
    skills = discover_skills(root)
    if not skills:
        print("no skills discovered", file=sys.stderr)
        return 1
    keys = set()
    schema = root / "config" / "schema.json"
    if schema.is_file():
        data = json.loads(schema.read_text(encoding="utf-8"))
        for group in data.get("groups", []):
            for key in group.get("keys", []):
                keys.add(key.get("name"))
    commit = git_commit(root)
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    failures = 0

    for host in hosts:
        spec = HOSTS.get(host)
        if not spec:
            print(f"unknown host: {host} (known: {', '.join(HOSTS)})", file=sys.stderr)
            failures += 1
            continue
        root_dir = out / host
        if root_dir.exists():
            shutil.rmtree(root_dir)
        skills_dir = root_dir / spec["skills_dir"]
        skills_dir.mkdir(parents=True)

        entries = []
        for skill in skills:
            copy_skill(skill, skills_dir)
            entries.append({
                "name": skill["name"],
                "partition": skill["partition"],
                "stage": skill["stage"],
                "path": f"{spec['skills_dir']}/{skill['name']}",
                "actions": skill["actions"],
                "artifacts": skill["artifacts"],
                "optional_requires": skill["optional_requires"],
                "parameters": skill.get("parameters"),
            })

        for extra in (".env.example", "README.md"):
            src = root / extra
            if src.is_file():
                shutil.copy2(src, root_dir / extra)
        if schema.is_file():
            (root_dir / "config").mkdir(exist_ok=True)
            shutil.copy2(schema, root_dir / "config" / "schema.json")

        manifest = {
            "schema": 1,
            "name": PLUGIN_NAME,
            "version": version,
            "host": host,
            "layout": spec["layout"],
            "generated_at": stamp,
            "source_commit": commit,
            "skills": entries,
            "env_keys": sorted(k for k in keys if k),
            "install_hint": _install_hint(host, spec),
        }
        (root_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        if "plugin" in spec:
            plugin = {
                "name": PLUGIN_NAME,
                "version": version,
                "description": "Research and development skills: retrieval, reasoning, output, verification.",
                "skills": "./skills",
            }
            target = root_dir / spec["plugin"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(plugin, ensure_ascii=False, indent=2) + "\n",
                              encoding="utf-8")

        if "plugin_src" in spec:
            src_dir = root / spec["plugin_src"]
            for name in ("package.json", "README.md"):
                if (src_dir / name).is_file():
                    shutil.copy2(src_dir / name, root_dir / name)
            if (src_dir / "lib").is_dir():
                shutil.copytree(src_dir / "lib", root_dir / "lib")
            pkg_path = root_dir / "package.json"
            if pkg_path.is_file():
                pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
                pkg["version"] = version
                pkg_path.write_text(json.dumps(pkg, ensure_ascii=False, indent=2) + "\n",
                                    encoding="utf-8")

        leaks = scan_secrets(root_dir)
        if (root_dir / ".env").exists():
            leaks.append(".env was copied into the bundle")
        status = "ok" if not leaks else "LEAK"
        print(f"{host:8} {len(entries):2} skills  layout={spec['layout']:8} {status}")
        for leak in leaks:
            print(f"   ! {leak}")
            failures += 1

    return 0 if failures == 0 else 1


def _install_hint(host: str, spec: dict) -> str:
    if host == "agents":
        return "copy .agents/skills/<name> into your project's .agents/skills/, or point the host at this dir"
    if host == "claude":
        return "install via the Claude plugin marketplace pointing at this bundle, or copy skills/ into the skills root"
    return "copy skills/<name> into the host's skills directory and reload"


def install_skills(src: Path, dest_root: Path, force: bool) -> int:
    """Copy built skill dirs into a host skills root (one dir per skill)."""
    if not src.is_dir():
        print(f"bundle skills dir not found: {src}", file=sys.stderr)
        return 1
    dest_root.mkdir(parents=True, exist_ok=True)
    installed = skipped = 0
    for skill in sorted(p for p in src.iterdir() if p.is_dir()):
        target = dest_root / skill.name
        if target.exists() and not force:
            skipped += 1
            continue
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(skill, target)
        installed += 1
    print(f"installed {installed} skills -> {dest_root} (skipped {skipped} existing; use --force to replace)")
    return 0


def check(root: Path, out: Path) -> int:
    problems: list[str] = []
    built = [d for d in out.iterdir() if d.is_dir()] if out.is_dir() else []
    if not built:
        print(f"nothing built under {out}", file=sys.stderr)
        return 1
    for host_dir in built:
        manifest_path = host_dir / "manifest.json"
        if not manifest_path.is_file():
            problems.append(f"{host_dir.name}: missing manifest.json")
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        skills_dir = host_dir / manifest["skills"][0]["path"].split("/")[0] if manifest["skills"] else None
        for entry in manifest.get("skills", []):
            skill_dir = host_dir / entry["path"]
            if not (skill_dir / "SKILL.md").is_file():
                problems.append(f"{host_dir.name}/{entry['name']}: missing SKILL.md")
            runtime = skill_dir / "runtime.json"
            if not runtime.is_file():
                problems.append(f"{host_dir.name}/{entry['name']}: missing runtime.json")
                continue
            spec = json.loads(runtime.read_text(encoding="utf-8"))
            for action in spec.get("actions", []):
                script = action.get("script")
                if script and not (skill_dir / script).is_file():
                    problems.append(f"{host_dir.name}/{entry['name']}: missing script {script}")
        leaks = scan_secrets(host_dir)
        problems.extend(f"{host_dir.name}: {leak}" for leak in leaks)
        print(f"{host_dir.name:8} manifest={manifest.get('version')} skills={len(manifest.get('skills', []))} leaks={len(leaks)}")
    if problems:
        for p in problems:
            print(f"  ! {p}", file=sys.stderr)
        return 1
    print("bundle check passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Qiyu-Brain plugin bundles.")
    parser.add_argument("--root", default=None, help="repo root (default: script's parent)")
    parser.add_argument("--out", default=None, help="output dir (default: <root>/dist)")
    parser.add_argument("--hosts", default="generic,agents,claude",
                        help=f"comma separated; known: {', '.join(HOSTS)}")
    parser.add_argument("--version", default=VERSION)
    parser.add_argument("--check", action="store_true", help="verify dist instead of building")
    parser.add_argument("--install", metavar="DEST", default=None,
                        help="after building, copy skills into a host skills root (DEST/<name>/)")
    parser.add_argument("--force", action="store_true",
                        help="with --install, replace existing skill dirs")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent
    out = Path(args.out).resolve() if args.out else root / "dist"
    if args.check:
        return check(root, out)
    out.mkdir(parents=True, exist_ok=True)
    hosts = [h.strip() for h in args.hosts.split(",") if h.strip()]
    rc = build(root, out, hosts, args.version)
    if args.install:
        rc = max(rc, install_skills(out / "generic" / "skills", Path(args.install).resolve(), args.force))
    return rc


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    sys.exit(main())
