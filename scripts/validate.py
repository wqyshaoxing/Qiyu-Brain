#!/usr/bin/env python3
"""Validate the Qiyu-Brain skill tree. Standard library only, no install step.

Usage:
    python scripts/validate.py
    python scripts/validate.py --root <repo>

Exit code 1 when any error is reported, 0 otherwise (warnings do not fail).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

STAGES = ("input", "reasoning", "output", "verify", "gateway")
LOOP_ROLES = {"entry", "transform", "render", "verify", "route"}
MODES = {"agent", "script", "hybrid"}
RESERVED_DIRS = {"scripts", "docs", "_core", "_memory", "_eval", "_profile",
                 "third-party", "search-out", "dist", "config"}
REQUIRED_FIELDS = ("name", "description", "domain", "stage", "loop_role",
                   "consumes", "produces", "deps")
LIST_FIELDS = {"stage", "consumes", "produces", "deps", "sources"}
MIN_DESC, MAX_DESC = 30, 200

THIRD_PARTY = "third-party"
REPO_ROOT = f"{THIRD_PARTY}/repos/"
STATUSES = {"listed", "evaluating", "adopted", "rejected", "archived"}
PROVENANCE_KINDS = {"code", "idea", "text", "data", "design"}
REQUIRED_ENTRY_FIELDS = ("id", "name", "url", "kind", "summary", "status", "added")

KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SNAKE = re.compile(r"^[a-z][a-z0-9_]*$")


class Problem(Exception):
    pass


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        raise Problem("SKILL.md 不以 '---' 开头，缺少 frontmatter")
    lines = text.split("\n")
    if lines[0].strip() != "---":
        raise Problem("第一行必须是单独的 '---'")
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return "\n".join(lines[1:idx]), "\n".join(lines[idx + 1:])
    raise Problem("frontmatter 没有闭合的 '---'")


def parse_frontmatter(block: str) -> dict[str, object]:
    data: dict[str, object] = {}
    for raw in block.split("\n"):
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")):
            raise Problem(f"frontmatter 只允许行内列表，不支持块缩进：{line.strip()!r}")
        if ":" not in line:
            raise Problem(f"无法解析的 frontmatter 行：{line!r}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key in data:
            raise Problem(f"frontmatter 字段重复：{key}")
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key] = [v.strip().strip("'\"") for v in inner.split(",") if v.strip()]
        else:
            data[key] = value.strip("'\"")
    return data


def _check_parameters(action: dict, where: str, skill_dir: Path, script: str | None,
                      errors: list[str], warnings: list[str]) -> None:
    """Validate the declared parameter schema and keep it in sync with --help.

    The schema is what a tool-registering host turns into a native tool; the
    cli binding is what a shell-only host turns into argv. Both must match the
    code, so the script's own --help is the executable source of truth.
    """
    params = action.get("parameters")
    if params is None:
        return
    if not isinstance(params, dict):
        errors.append(f"{where}.parameters 必须是对象")
        return
    props = params.get("properties")
    required = params.get("required", [])
    if not isinstance(props, dict) or not props:
        errors.append(f"{where}.parameters.properties 不能为空")
        return
    if not isinstance(required, list):
        errors.append(f"{where}.parameters.required 必须是数组")
        required = []
    for name in required:
        if name not in props:
            errors.append(f"{where}.parameters.required 含未声明参数 '{name}'")
    for pname, pspec in props.items():
        if not isinstance(pspec, dict):
            errors.append(f"{where}.parameters.properties.{pname} 必须是对象")
            continue
        if "type" not in pspec:
            errors.append(f"{where}.parameters.properties.{pname} 缺少 type")
        cli = pspec.get("cli")
        if not isinstance(cli, str) or not cli.startswith("--"):
            errors.append(f"{where}.parameters.properties.{pname}.cli 必须以 -- 开头")

    if not script:
        return
    script_path = skill_dir / script
    if not script_path.is_file():
        return
    try:
        proc = subprocess.run([sys.executable, str(script_path), "--help"],
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=25,
                              env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        help_text = (proc.stdout or "") + (proc.stderr or "")
    except Exception as exc:  # noqa: BLE001 - introspection is best effort
        warnings.append(f"{where}: 无法运行脚本 --help（{type(exc).__name__}），跳过参数同步检查")
        return
    for pname, pspec in props.items():
        cli = pspec.get("cli") if isinstance(pspec, dict) else None
        if isinstance(cli, str) and cli not in help_text:
            errors.append(f"{where}: 参数 '{pname}' 绑定 {cli}，但脚本 --help 中没有该参数")


def check_skill(skill_dir: Path, domain: str, stage_dir: str | None,
                errors: list[str], warnings: list[str]) -> dict[str, object] | None:
    rel = skill_dir.as_posix()
    skill_md = skill_dir / "SKILL.md"
    runtime = skill_dir / "runtime.json"
    if not skill_md.is_file():
        errors.append(f"{rel}: 缺少 SKILL.md")
        return None
    try:
        meta_block, body = split_frontmatter(read_text(skill_md))
        meta = parse_frontmatter(meta_block)
    except Problem as exc:
        errors.append(f"{rel}/SKILL.md: {exc}")
        return None

    for field in REQUIRED_FIELDS:
        if field not in meta:
            errors.append(f"{rel}: frontmatter 缺少 '{field}'")
    for field in LIST_FIELDS:
        if field in meta and not isinstance(meta[field], list):
            errors.append(f"{rel}: '{field}' 必须是行内列表，如 [a, b]")

    name = meta.get("name")
    if not isinstance(name, str) or not KEBAB.match(name):
        errors.append(f"{rel}: name 不是 kebab-case：{name!r}")
    elif name != skill_dir.name:
        errors.append(f"{rel}: name '{name}' 与目录名 '{skill_dir.name}' 不一致")

    if meta.get("domain") != domain:
        errors.append(f"{rel}: domain '{meta.get('domain')}' 与所在分区 '{domain}' 不一致")

    stages = meta.get("stage") or []
    if not isinstance(stages, list) or not stages:
        errors.append(f"{rel}: stage 不能为空")
    else:
        for st in stages:
            if st not in STAGES:
                errors.append(f"{rel}: stage 取值非法：{st!r}")
        if stage_dir is None:
            if list(stages) != ["gateway"]:
                errors.append(f"{rel}: 扁平分区的 stage 必须为 [gateway]，实际为 {stages}")
        else:
            if "gateway" in stages:
                errors.append(f"{rel}: 只有扁平分区可以使用 stage: [gateway]")
            if stage_dir not in stages:
                errors.append(f"{rel}: 所在目录 '{stage_dir}' 不在 stage {stages} 中")

    if meta.get("loop_role") not in LOOP_ROLES:
        errors.append(f"{rel}: loop_role 取值非法：{meta.get('loop_role')!r}")

    desc = meta.get("description")
    if not isinstance(desc, str) or not desc.strip():
        errors.append(f"{rel}: description 为空")
    elif not (MIN_DESC <= len(desc) <= MAX_DESC):
        warnings.append(f"{rel}: description 长度 {len(desc)}，建议 {MIN_DESC}-{MAX_DESC}")

    produces = meta.get("produces") or []
    if isinstance(produces, list) and not produces:
        warnings.append(f"{rel}: produces 为空，确认这是纯判定技能")

    sources = meta.get("sources")
    if sources is None:
        sources = []
    elif not isinstance(sources, list):
        errors.append(f"{rel}: 'sources' 必须是行内列表")
        sources = []

    deps = meta.get("deps") or []
    if not isinstance(deps, list):
        errors.append(f"{rel}: 'deps' 必须是行内列表")
        deps = []

    for line in ("## When to use", "## Boundary", "## Workflow", "## Artifacts"):
        if line not in body:
            errors.append(f"{rel}/SKILL.md: 正文缺少 '{line}'")

    if not runtime.is_file():
        errors.append(f"{rel}: 缺少 runtime.json")
        return {"name": name, "stages": stages, "sources": sources, "deps": deps}

    try:
        spec = json.loads(read_text(runtime))
    except json.JSONDecodeError as exc:
        errors.append(f"{rel}/runtime.json: 不是合法 JSON（{exc}）")
        return {"name": name, "stages": stages, "sources": sources, "deps": deps}
    if not isinstance(spec, dict):
        errors.append(f"{rel}/runtime.json: 顶层必须是对象")
        return {"name": name, "stages": stages, "sources": sources, "deps": deps}

    if spec.get("schema") != 1:
        errors.append(f"{rel}/runtime.json: schema 必须为 1")

    mode = spec.get("mode")
    if mode not in MODES:
        errors.append(f"{rel}/runtime.json: mode 非法：{mode!r}")

    actions = spec.get("actions")
    if not isinstance(actions, list):
        errors.append(f"{rel}/runtime.json: actions 必须是数组")
        actions = []
    if mode == "agent" and actions:
        warnings.append(f"{rel}: mode 为 agent 但声明了 actions")
    if mode in {"script", "hybrid"} and not actions:
        warnings.append(f"{rel}: mode 为 {mode} 但没有声明任何 action")
    seen_actions: set[str] = set()
    for idx, action in enumerate(actions):
        where = f"{rel}/runtime.json: actions[{idx}]"
        if not isinstance(action, dict):
            errors.append(f"{where} 必须是对象")
            continue
        aname = action.get("name")
        if not isinstance(aname, str) or not KEBAB.match(aname):
            errors.append(f"{where}.name 不是 kebab-case：{aname!r}")
        elif aname in seen_actions:
            errors.append(f"{where}.name 重复：{aname}")
        else:
            seen_actions.add(aname)
        script = action.get("script")
        if not isinstance(script, str) or not script.strip():
            errors.append(f"{where}.script 缺失")
        elif not (skill_dir / script).is_file():
            errors.append(f"{where}.script 指向的文件不存在：{script}")
        if "external" in action and not isinstance(action["external"], bool):
            errors.append(f"{where}.external 必须是布尔值")
        _check_parameters(action, where, skill_dir, script, errors, warnings)

    artifacts = spec.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append(f"{rel}/runtime.json: artifacts 必须是数组")
        artifacts = []
    roles: set[str] = set()
    required_roles: set[str] = set()
    for idx, art in enumerate(artifacts):
        where = f"{rel}/runtime.json: artifacts[{idx}]"
        if not isinstance(art, dict):
            errors.append(f"{where} 必须是对象")
            continue
        role = art.get("role")
        if not isinstance(role, str) or not SNAKE.match(role):
            errors.append(f"{where}.role 不是 snake_case：{role!r}")
            continue
        if role in roles:
            errors.append(f"{where}.role 重复：{role}")
        roles.add(role)
        if not isinstance(art.get("required"), bool):
            errors.append(f"{where}.required 必须是布尔值")
        elif art["required"]:
            required_roles.add(role)
        if not isinstance(art.get("kind"), str) or not art["kind"].strip():
            errors.append(f"{where}.kind 缺失")

    for role in produces if isinstance(produces, list) else []:
        if role not in roles:
            errors.append(f"{rel}: produces 中的 '{role}' 未在 runtime.json artifacts 声明")
    for role in required_roles:
        if isinstance(produces, list) and role not in produces:
            errors.append(f"{rel}: required artifact '{role}' 未写入 produces")

    completion = spec.get("completion")
    if not isinstance(completion, dict):
        errors.append(f"{rel}/runtime.json: completion 必须是对象")
    else:
        for key in ("requires_review", "hash_bound"):
            if not isinstance(completion.get(key), bool):
                errors.append(f"{rel}/runtime.json: completion.{key} 必须是布尔值")

    return {"name": name, "stages": stages, "sources": sources, "deps": deps}


def load_json(path: Path, errors: list[str]) -> object | None:
    label = path.as_posix()
    if not path.is_file():
        errors.append(f"{label}: 文件不存在")
        return None
    try:
        return json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        errors.append(f"{label}: 不是合法 JSON（{exc}）")
        return None


def check_third_party(root: Path, skill_names: set[str],
                      sources_of: dict[str, list[str]],
                      errors: list[str], warnings: list[str]) -> int:
    base = root / THIRD_PARTY
    if not base.is_dir():
        warnings.append(f"{THIRD_PARTY}: 目录不存在")
        return 0

    ignore = base / ".gitignore"
    if not ignore.is_file():
        warnings.append(f"{THIRD_PARTY}: 缺少 .gitignore，克隆的仓库可能被提交")
    elif "repos/" not in read_text(ignore):
        warnings.append(f"{THIRD_PARTY}/.gitignore: 未忽略 repos/")

    registry = load_json(base / "registry.json", errors)
    ids: set[str] = set()
    license_unknown: set[str] = set()
    if isinstance(registry, dict):
        if registry.get("schema") != 1:
            errors.append(f"{THIRD_PARTY}/registry.json: schema 必须为 1")
        entries = registry.get("entries")
        if not isinstance(entries, list):
            errors.append(f"{THIRD_PARTY}/registry.json: entries 必须是数组")
            entries = []
        for idx, entry in enumerate(entries):
            where = f"{THIRD_PARTY}/registry.json: entries[{idx}]"
            if not isinstance(entry, dict):
                errors.append(f"{where} 必须是对象")
                continue
            eid = entry.get("id")
            if not isinstance(eid, str) or not KEBAB.match(eid):
                errors.append(f"{where}.id 不是 kebab-case：{eid!r}")
                eid = None
            elif eid in ids:
                errors.append(f"{where}.id 重复：{eid}")
            else:
                ids.add(eid)
            for field in REQUIRED_ENTRY_FIELDS:
                if not isinstance(entry.get(field), str) or not str(entry.get(field)).strip():
                    errors.append(f"{where}.{field} 缺失或为空")
            url = entry.get("url")
            if isinstance(url, str) and not url.startswith("https://"):
                errors.append(f"{where}.url 必须以 https:// 开头")
            if entry.get("status") not in STATUSES:
                errors.append(f"{where}.status 非法：{entry.get('status')!r}，应为 {sorted(STATUSES)}")
            local_path = entry.get("local_path")
            if local_path is not None:
                if not isinstance(local_path, str) or not local_path.startswith(REPO_ROOT):
                    errors.append(f"{where}.local_path 必须以 {REPO_ROOT} 开头")
                elif eid and local_path != f"{REPO_ROOT}{eid}":
                    errors.append(f"{where}.local_path 应为 {REPO_ROOT}{eid}")
            if entry.get("license_checked") is True and entry.get("license") in (None, "", "unknown"):
                errors.append(f"{where}: license_checked 为 true 但 license 仍是 unknown")
            if entry.get("license") in (None, "", "unknown"):
                if eid:
                    license_unknown.add(eid)

    provenance = load_json(base / "provenance.json", errors)
    cited_by_skill: dict[str, set[str]] = {}
    if isinstance(provenance, dict):
        if provenance.get("schema") != 1:
            errors.append(f"{THIRD_PARTY}/provenance.json: schema 必须为 1")
        entries = provenance.get("entries")
        if not isinstance(entries, list):
            errors.append(f"{THIRD_PARTY}/provenance.json: entries 必须是数组")
            entries = []
        for idx, entry in enumerate(entries):
            where = f"{THIRD_PARTY}/provenance.json: entries[{idx}]"
            if not isinstance(entry, dict):
                errors.append(f"{where} 必须是对象")
                continue
            rid = entry.get("registry_id")
            if rid not in ids:
                errors.append(f"{where}.registry_id 未在 registry.json 中登记：{rid!r}")
            skill = entry.get("skill")
            if skill not in skill_names:
                errors.append(f"{where}.skill 不是本仓库技能：{skill!r}")
            elif isinstance(skill, str):
                cited_by_skill.setdefault(skill, set()).add(str(rid))
            if entry.get("kind") not in PROVENANCE_KINDS:
                errors.append(f"{where}.kind 非法：{entry.get('kind')!r}，应为 {sorted(PROVENANCE_KINDS)}")
            if not entry.get("commit") and not entry.get("url"):
                errors.append(f"{where}: commit 与 url 至少要有一个才能追溯")
            if not isinstance(entry.get("what"), str) or not str(entry.get("what")).strip():
                errors.append(f"{where}.what 缺失：必须说明借用了什么")
            if rid in license_unknown and entry.get("kind") == "code":
                warnings.append(f"{where}: 上游许可未确认却登记为 code 借用，确认后再使用")

    for skill, ids_used in sources_of.items():
        for rid in ids_used:
            if rid not in ids:
                errors.append(f"{skill}: frontmatter sources 中的 '{rid}' 未在 registry.json 登记")
        if skill not in cited_by_skill:
            warnings.append(f"{skill}: 声明了 sources 但 provenance.json 没有对应记录")

    for skill, used in cited_by_skill.items():
        declared = set(sources_of.get(skill, []))
        for rid in used:
            if rid not in declared:
                warnings.append(f"{skill}: provenance.json 记录了 {rid}，但 frontmatter sources 未声明")

    unverified = sum(
        1 for entry in (registry.get("entries") if isinstance(registry, dict) else []) or []
        if isinstance(entry, dict) and entry.get("verified") is not True
    )
    if ids and unverified == len(ids):
        warnings.append(f"{THIRD_PARTY}: 全部 {len(ids)} 条登记均 verified=false，采用前需复核")
    return len(ids)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Qiyu-Brain skill tree.")
    parser.add_argument("--root", default=None, help="仓库根目录，默认为脚本上一级")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent
    errors: list[str] = []
    warnings: list[str] = []
    registry: dict[str, str] = {}
    results: list[dict[str, object]] = []

    domain_dirs = sorted(
        d for d in root.iterdir()
        if d.is_dir() and d.name not in RESERVED_DIRS and not d.name.startswith("_")
        and not d.name.startswith(".")
    )
    if not domain_dirs:
        errors.append(f"{root}: 未找到任何领域目录")

    for domain_dir in domain_dirs:
        domain = domain_dir.name
        if not KEBAB.match(domain):
            errors.append(f"{domain}: 分区目录名不是 kebab-case")
        if not (domain_dir / "README.md").is_file():
            warnings.append(f"{domain}: 缺少分区 README.md")
        children = sorted(d for d in domain_dir.iterdir() if d.is_dir() and not d.name.startswith("."))
        if not children:
            warnings.append(f"{domain}: 没有任何技能目录（骨架分区）")
            continue
        flat = any((child / "SKILL.md").is_file() for child in children)
        if flat and any(child.name in STAGES for child in children):
            errors.append(f"{domain}: 不能同时包含阶段目录和技能目录")

        pairs: list[tuple[Path, str | None]] = []
        if flat:
            for child in children:
                if (child / "SKILL.md").is_file():
                    pairs.append((child, None))
                else:
                    errors.append(f"{domain}/{child.name}: 扁平分区中只能放技能目录")
        else:
            for stage_dir in children:
                if stage_dir.name not in STAGES:
                    errors.append(f"{domain}/{stage_dir.name}: 不是合法阶段名，应为 {STAGES}")
                    continue
                for skill_dir in sorted(d for d in stage_dir.iterdir() if d.is_dir() and not d.name.startswith(".")):
                    pairs.append((skill_dir, stage_dir.name))

        for skill_dir, stage_name in pairs:
            info = check_skill(skill_dir, domain, stage_name, errors, warnings)
            if not info:
                continue
            name = info.get("name")
            if isinstance(name, str):
                if name in registry:
                    errors.append(f"{name}: 重复出现于 {registry[name]} 和 {skill_dir.as_posix()}")
                else:
                    registry[name] = skill_dir.as_posix()
            info["domain"] = domain
            results.append(info)

    sources_of = {
        str(r.get("name")): list(r.get("sources") or [])
        for r in results
        if r.get("sources")
    }
    by_name = {str(r.get("name")): r for r in results if r.get("name")}
    domain_of = {name: str(info.get("domain")) for name, info in by_name.items()}

    for name, info in by_name.items():
        for dep in info.get("deps") or []:
            if dep not in by_name:
                errors.append(f"{name}: deps 指向不存在的技能 '{dep}'")
                continue
            if domain_of.get(name) == "shared" and domain_of.get(dep) != "shared":
                errors.append(f"{name}: shared 只能依赖 shared，不能依赖 '{dep}'（{domain_of.get(dep)}）")

    state: dict[str, int] = {}

    def walk(node: str, stack: list[str]) -> None:
        state[node] = 1
        for dep in by_name[node].get("deps") or []:
            if dep not in by_name:
                continue
            if state.get(dep) == 1:
                errors.append("依赖成环: " + " -> ".join(stack + [dep]))
            elif state.get(dep, 0) == 0:
                walk(dep, stack + [dep])
        state[node] = 2

    for node in by_name:
        if state.get(node, 0) == 0:
            walk(node, [node])

    dep_edges = sum(
        len([d for d in (by_name[n].get("deps") or []) if d in by_name]) for n in by_name
    )
    third_party_count = check_third_party(root, set(registry), sources_of, errors, warnings)

    index = root / "INDEX.md"
    if not index.is_file():
        errors.append("缺少 INDEX.md")
    else:
        index_text = read_text(index)
        for name in registry:
            if name not in index_text:
                warnings.append(f"{name}: 未在 INDEX.md 登记")

    ordered = sorted(results, key=lambda r: str(r.get("name")))
    report = {
        "skills": len(ordered),
        "third_party": third_party_count,
        "deps_edges": dep_edges,
        "errors": errors,
        "warnings": warnings,
        "registry": [{"name": r.get("name"), "stage": r.get("stages")} for r in ordered],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
