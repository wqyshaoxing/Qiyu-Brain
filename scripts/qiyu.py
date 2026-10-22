#!/usr/bin/env python3
"""Qiyu-Brain lifecycle: build, install, status, doctor, uninstall.

Skills are the product; this CLI is the system boundary around them. Without
it, installing is "copy 12 folders" and nobody can answer which version is
where, or whether the installed copy drifted from source.

    python scripts/qiyu.py status
    python scripts/qiyu.py install --host agents --root <skills-root>
    python scripts/qiyu.py adopt --host dsh --root <skills-root>
    python scripts/qiyu.py doctor
    python scripts/qiyu.py uninstall --host dsh

State lives in <repo>/.qiyu/state.json (gitignored), never inside a host's
skill root, so hosts see only skill directories.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_plugin  # noqa: E402  (same directory, no package)

STATE_SCHEMA = 1
SKIP = {".git", "__pycache__", "dist", "search-out", "_qiyu", ".qiyu"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def state_path(root: Path) -> Path:
    return root / ".qiyu" / "state.json"


def load_state(root: Path) -> dict:
    path = state_path(root)
    if not path.is_file():
        return {"schema": STATE_SCHEMA, "installs": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"schema": STATE_SCHEMA, "installs": {}}
    data.setdefault("installs", {})
    return data


def save_state(root: Path, state: dict) -> None:
    path = state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def skill_hashes(skills: list[dict]) -> dict[str, str]:
    return {s["name"]: sha256_file(s["source"] / "SKILL.md") for s in skills}


def version_of(root: Path) -> str:
    marker = root / "VERSION"
    if marker.is_file():
        text = marker.read_text(encoding="utf-8").strip()
        if text:
            return text
    return "0.0.0"


# ------------------------------------------------------------------- commands

def cmd_install(root: Path, args) -> int:
    host = args.host
    dest = Path(args.root).resolve()
    skills = build_plugin.discover_skills(root)
    if not skills:
        print("no skills discovered", file=sys.stderr)
        return 1
    dest.mkdir(parents=True, exist_ok=True)

    installed, replaced, skipped = [], [], []
    for skill in skills:
        target = dest / skill["name"]
        if target.exists():
            if not args.force:
                skipped.append(skill["name"])
                continue
            shutil.rmtree(target)
            replaced.append(skill["name"])
        shutil.copytree(skill["source"], target,
                        ignore=shutil.ignore_patterns(*SKIP, ".env", "*.pyc"))
        installed.append(skill["name"])

    state = load_state(root)
    state["installs"][host] = {
        "root": str(dest),
        "version": args.version,
        "commit": build_plugin.git_commit(root),
        "installed_at": now(),
        "skills": skill_hashes([s for s in skills if s["name"] in installed or s["name"] in replaced]),
        "layout": build_plugin.HOSTS.get(host, {}).get("layout", "custom"),
    }
    save_state(root, state)

    print(f"{host}: installed {len(installed)}, replaced {len(replaced)}, skipped {len(skipped)} -> {dest}")
    if skipped:
        print(f"  skipped existing: {', '.join(skipped)} (use --force)")
    return 0


def cmd_adopt(root: Path, args) -> int:
    """Register an existing install without copying anything."""
    dest = Path(args.root).resolve()
    state = load_state(root)
    skills = build_plugin.discover_skills(root)
    present = {}
    for skill in skills:
        md = dest / skill["name"] / "SKILL.md"
        if md.is_file():
            present[skill["name"]] = sha256_file(md)
    state["installs"][args.host] = {
        "root": str(dest),
        "version": args.version,
        "commit": build_plugin.git_commit(root),
        "installed_at": now(),
        "skills": present,
        "layout": "adopted",
    }
    save_state(root, state)
    print(f"{args.host}: adopted {len(present)} skills at {dest}")
    return 0


def cmd_status(root: Path, args) -> int:
    state = load_state(root)
    installs = state.get("installs", {})
    if not installs:
        print("no installs recorded; run `qiyu.py install` or `qiyu.py adopt`")
        return 0

    current = version_of(root)
    skills = build_plugin.discover_skills(root)
    source = skill_hashes(skills)
    commit = build_plugin.git_commit(root)
    problems = 0

    for host, rec in sorted(installs.items()):
        dest = Path(rec.get("root", ""))
        marks = {"insync": 0, "source-newer": 0, "modified": 0, "missing": 0}
        for name, recorded in rec.get("skills", {}).items():
            md = dest / name / "SKILL.md"
            if not md.is_file():
                marks["missing"] += 1
                continue
            current_hash = sha256_file(md)
            if current_hash != recorded:
                marks["modified"] += 1
            elif source.get(name) and source[name] != current_hash:
                marks["source-newer"] += 1
            else:
                marks["insync"] += 1

        untracked = []
        if dest.is_dir():
            untracked = sorted(p.name for p in dest.iterdir()
                               if p.is_dir() and p.name not in rec.get("skills", {})
                               and (p / "SKILL.md").is_file())
        new_in_source = sorted(set(source) - set(rec.get("skills", {})))

        print(f"\n{host}")
        print(f"  root      {dest}")
        print(f"  installed {rec.get('version')} @ {rec.get('commit') or 'n/a'}  ({rec.get('installed_at')})")
        print(f"  source    {current} @ {commit or 'n/a'}")
        print(f"  skills    {len(rec.get('skills', {}))} recorded | "
              f"insync={marks['insync']} source-newer={marks['source-newer']} "
              f"modified={marks['modified']} missing={marks['missing']}")
        if rec.get("version") != current:
            print(f"  ! version differs ({rec.get('version')} -> {current})")
            problems += 1
        if marks["source-newer"]:
            print("  ! source changed since install; rerun install --force")
            problems += 1
        if marks["modified"]:
            print("  ! installed copy edited locally; it will differ from source")
            problems += 1
        if marks["missing"]:
            print("  ! recorded skills missing on disk")
            problems += 1
        if new_in_source:
            print(f"  + new in source, not installed: {', '.join(new_in_source)}")
        if untracked:
            print(f"  ? untracked skill dirs: {', '.join(untracked)}")

    print(f"\n{'OK' if problems == 0 else str(problems) + ' issue(s)'}")
    return 0 if problems == 0 else 1


def cmd_doctor(root: Path, args) -> int:
    skills = build_plugin.discover_skills(root)
    failures = 0
    print("== executable actions ==")
    for skill in skills:
        runtime = skill["source"] / "runtime.json"
        if not runtime.is_file():
            continue
        spec = json.loads(runtime.read_text(encoding="utf-8"))
        for action in spec.get("actions", []):
            script = action.get("script")
            if not script:
                continue
            path = skill["source"] / script
            if not path.is_file():
                print(f"  {skill['name']:24} MISSING {script}")
                failures += 1
                continue
            try:
                proc = subprocess.run([sys.executable, str(path), "--help"],
                                      capture_output=True, text=True, encoding="utf-8",
                                      errors="replace", timeout=25,
                                      env={**os.environ, "PYTHONIOENCODING": "utf-8"})
                help_text = (proc.stdout or "") + (proc.stderr or "")
            except Exception as exc:  # noqa: BLE001
                print(f"  {skill['name']:24} cannot run --help: {type(exc).__name__}")
                failures += 1
                continue
            missing = [p["cli"] for p in (action.get("parameters", {}).get("properties") or {}).values()
                       if isinstance(p, dict) and p.get("cli") and p["cli"] not in help_text]
            state = "ok" if not missing else f"MISSING {', '.join(missing)}"
            print(f"  {skill['name']:24} {script:28} {state}")
            if missing:
                failures += 1

    print("\n== credentials ==")
    schema = root / "config" / "schema.json"
    env = dict(os.environ)
    env_file = root / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8-sig").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                env.setdefault(k.strip(), v.strip())
    if schema.is_file():
        data = json.loads(schema.read_text(encoding="utf-8"))
        for group in data.get("groups", []):
            keys = group.get("keys", [])
            if not keys:
                continue
            have = sum(1 for k in keys if env.get(k.get("name", "")))
            missing_required = [k["name"] for k in keys
                                if k.get("required") and not env.get(k.get("name", ""))]
            print(f"  {group.get('title', group.get('id')):12} {have}/{len(keys)} set"
                  + (f"  REQUIRED missing: {', '.join(missing_required)}" if missing_required else ""))
            if missing_required:
                failures += 1

    print(f"\n{'OK' if failures == 0 else str(failures) + ' issue(s)'}")
    return 0 if failures == 0 else 1


def cmd_uninstall(root: Path, args) -> int:
    state = load_state(root)
    rec = state.get("installs", {}).get(args.host)
    if not rec:
        print(f"{args.host} is not recorded in {state_path(root)}", file=sys.stderr)
        return 1
    dest = Path(rec["root"])
    removed = 0
    for name in rec.get("skills", {}):
        target = dest / name
        if target.is_dir():
            shutil.rmtree(target)
            removed += 1
    del state["installs"][args.host]
    save_state(root, state)
    print(f"{args.host}: removed {removed} skill dirs from {dest}")
    return 0


def cmd_build(root: Path, args) -> int:
    out = root / "dist"
    hosts = [h.strip() for h in args.hosts.split(",") if h.strip()]
    return build_plugin.build(root, out, hosts, args.version)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Qiyu-Brain lifecycle.")
    parser.add_argument("--root", default=None, help="repo root")
    parser.add_argument("--version", default=None, help="version label (default: plugin/package.json)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="build host bundles into dist/")
    p_build.add_argument("--hosts", default="generic,agents,claude")

    for name, extra in (("install", "install skills into a host root"),
                        ("adopt", "register an existing install")):
        p = sub.add_parser(name, help=extra)
        p.add_argument("--host", required=True, help=f"label, e.g. {', '.join(build_plugin.HOSTS)}")
        p.add_argument("--root", required=True, dest="root_path", help="host skills root")
        p.add_argument("--force", action="store_true")

    p_un = sub.add_parser("uninstall", help="remove a recorded install")
    p_un.add_argument("--host", required=True)

    sub.add_parser("status", help="compare recorded installs with source")
    sub.add_parser("doctor", help="check scripts and credentials")

    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else repo_root()
    args.version = args.version or version_of(root)

    if args.command == "build":
        return cmd_build(root, args)
    if args.command == "install":
        args.root = args.root_path
        return cmd_install(root, args)
    if args.command == "adopt":
        args.root = args.root_path
        return cmd_adopt(root, args)
    if args.command == "status":
        return cmd_status(root, args)
    if args.command == "doctor":
        return cmd_doctor(root, args)
    if args.command == "uninstall":
        return cmd_uninstall(root, args)
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    sys.exit(main())
