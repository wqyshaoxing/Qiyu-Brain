#!/usr/bin/env python3
"""Traceable PDF archival through Zotero's cloud Web API (default: offline dry run)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from zotero_web import Client, WebError, object_key, valid_key


def utc():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


@contextmanager
def manifest_lock(path):
    """OS-held lock is released on process exit, including runtime cancellation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(path.suffix + ".lock").open("a+b") as stream:
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise WebError("This manifest is in use by another import; wait for that process") from exc
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def fingerprint(path):
    from pypdf import PdfReader
    from pypdf.errors import PyPdfError
    if path.stat().st_size > 200 * 1024 * 1024:
        raise WebError("PDF exceeds the 200 MiB import limit")
    with path.open("rb") as stream:
        if stream.read(5) != b"%PDF-":
            raise WebError("Not a PDF; HTML/login responses must not be archived")
    try:
        reader = PdfReader(path, strict=True)
        if reader.is_encrypted or not reader.pages:
            raise WebError("PDF is encrypted or has no pages")
        for page in reader.pages:
            _ = page.mediabox
    except (PyPdfError, ValueError, KeyError) as exc:
        raise WebError("PDF failed strict structure validation") from exc
    sha, md5 = hashlib.sha256(), hashlib.md5(usedforsecurity=False)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
            md5.update(block)
    return {"sha256": sha.hexdigest(), "md5": md5.hexdigest(), "bytes": path.stat().st_size,
            "pages": len(reader.pages), "mtime": int(path.stat().st_mtime * 1000),
            "validation": "PDF header, strict parser and all page objects"}


def load_metadata(path, source):
    if path is None:
        return {}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict) or not isinstance(value.get("papers"), list):
        raise WebError("Metadata must contain a papers array")
    result = {}
    for paper in value["papers"]:
        if not isinstance(paper, dict) or not isinstance(paper.get("file"), str):
            raise WebError("Each metadata entry requires a source-relative file")
        target = (source / paper["file"]).resolve()
        if Path(paper["file"]).is_absolute() or not target.is_relative_to(source):
            raise WebError("Metadata file paths must stay inside the source directory")
        data = paper.get("data")
        if not isinstance(data, dict) or not isinstance(data.get("title"), str) or not data["title"].strip():
            raise WebError("Metadata requires a reviewed title and Zotero data object")
        if not data.get("itemType") or data["itemType"] in {"attachment", "note", "annotation"}:
            raise WebError("Metadata itemType must be a bibliographic item type")
        if not isinstance(paper.get("provenance"), str) or not paper["provenance"].strip():
            raise WebError("Record the source and review basis in metadata.provenance")
        if target in result:
            raise WebError("Duplicate metadata entry for one file")
        if any(field in data for field in ("key", "version", "collections", "tags", "relations", "parentItem", "dateAdded", "dateModified")):
            raise WebError("Metadata must not set object keys, versions or library membership")
        result[target] = {"data": data, "provenance": paper["provenance"]}
    return result


def metadata_hash(metadata):
    return hashlib.sha256(json.dumps(metadata, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def tags(item):
    return {tag["tag"] for tag in item.get("data", {}).get("tags", []) if isinstance(tag, dict) and isinstance(tag.get("tag"), str)}


def ensure_membership(client, item, collection_key, wanted_tags, *, child=False):
    current = tags(item)
    fields = {}
    if not wanted_tags <= current:
        # Retain existing tag types, and never replace the user's other tags.
        fields["tags"] = item["data"].get("tags", []) + [{"tag": tag} for tag in sorted(wanted_tags - current)]
    if not child:
        collections = item["data"].get("collections", [])
        if collection_key not in collections:
            fields["collections"] = collections + [collection_key]
    if fields:
        client.patch(item, fields)
        item = client.get("items", item["key"])
    if not item or not wanted_tags <= tags(item) or (not child and collection_key not in item["data"].get("collections", [])):
        raise WebError("Remote collection/tag verification failed")
    return item


def collection(client, batch, args, save):
    if args.collection_key:
        item = client.get("collections", args.collection_key)
        if not item:
            raise WebError("Requested collection does not exist in the target library")
        if batch.get("collection_key") and batch["collection_key"] != item["key"]:
            raise WebError("This batch already has a different collection; use a new batch or reconcile it")
    elif batch.get("collection_key"):
        item = client.get("collections", batch["collection_key"])
        if item and (item["data"].get("name") != batch["collection_name"] or (item["data"].get("parentCollection") or None) != args.parent_collection):
            raise WebError("Saved collection was changed remotely; reconcile before continuing")
        if not item:
            # The key was persisted before a POST, so a lost reply can be retried safely.
            if batch.get("collection_verified"):
                raise WebError("Previously verified collection was deleted remotely")
            item = client.create("collections", {"key": batch["collection_key"], "name": batch["collection_name"],
                                 "parentCollection": args.parent_collection or False}, batch["write_token"])
    else:
        if args.parent_collection and not client.get("collections", args.parent_collection):
            raise WebError("Parent collection does not exist in the target library")
        matches = [item for item in client.pages("collections") if item["data"].get("name") == batch["collection_name"]
                   and (item["data"].get("parentCollection") or None) == args.parent_collection]
        if len(matches) > 1:
            raise WebError("Multiple matching timestamp collections; select one explicitly by --collection-key")
        if matches:
            item = matches[0]
        else:
            batch["collection_key"] = object_key()
            save("collection_key_reserved")
            item = client.create("collections", {"key": batch["collection_key"], "name": batch["collection_name"],
                                 "parentCollection": args.parent_collection or False}, batch["write_token"])
    batch.update(collection_key=item["key"], collection_verified=True)
    save("collection_verified")
    return item["key"]


def import_pdf(client, path, details, metadata, entry, collection_key, wanted_tags, save):
    content_tag = "boomskills:sha256:" + details["sha256"]
    item = client.get("items", entry["attachment_key"]) if entry.get("attachment_key") else None
    if entry.get("attachment_key") and not item and entry.get("attachment_created"):
        raise WebError("Previously created attachment was deleted remotely; reconcile the manifest")
    if not item and not entry.get("attachment_key"):
        matches = [item for item in client.pages("items", tag=content_tag, itemType="attachment") if content_tag in tags(item)]
        if len(matches) > 1:
            raise WebError("Multiple attachments share this content tag; reconcile instead of importing another copy")
        if matches:
            item = matches[0]
            entry.update(attachment_key=item["key"], parent_key=item["data"].get("parentItem") or None, reused=True)
            save("remote_content_match")
    if item:
        if item["data"].get("itemType") != "attachment" or content_tag not in tags(item) or item["data"].get("linkMode") != "imported_file":
            raise WebError("Saved attachment identity does not match the validated PDF")
        remote_parent = item["data"].get("parentItem") or None
        if entry.get("parent_key") != remote_parent:
            raise WebError("Attachment parent was changed remotely; reconcile before continuing")
        if metadata and not remote_parent:
            raise WebError("Existing standalone attachment needs a reviewed metadata migration; no duplicate will be created")
        entry["attachment_created"] = True
        if item["data"].get("md5") == details["md5"]:
            entry["reused"] = True
    else:
        parent = None
        if metadata:
            template = client.template(metadata["data"]["itemType"])
            if set(metadata["data"]) - set(template):
                raise WebError("Metadata includes unsupported fields for this Zotero item type")
            if not entry.get("parent_key"):
                entry["parent_key"] = object_key()
                entry["parent_write_token"] = uuid.uuid4().hex
                save("parent_key_reserved")
            parent = client.get("items", entry["parent_key"])
            if parent:
                if parent["data"].get("itemType") != metadata["data"]["itemType"] or parent["data"].get("title") != metadata["data"]["title"]:
                    raise WebError("Saved parent identity does not match reviewed metadata")
            else:
                if entry.get("parent_created"):
                    raise WebError("Previously created parent was deleted remotely")
                parent_data = {**template, **metadata["data"], "key": entry["parent_key"],
                               "tags": [{"tag": tag} for tag in sorted(wanted_tags)], "collections": [collection_key]}
                parent = client.create("items", parent_data, entry["parent_write_token"])
            entry["parent_created"] = True
            save("parent_verified")
        if not entry.get("attachment_key"):
            entry.update(attachment_key=object_key(), attachment_write_token=uuid.uuid4().hex)
            save("attachment_key_reserved")
        attachment = client.template("attachment", "imported_file")
        attachment.update(key=entry["attachment_key"], title="PDF", filename=f"paper-{details['sha256'][:12]}.pdf",
                          contentType="application/pdf", tags=[{"tag": tag} for tag in sorted(wanted_tags | {content_tag})])
        if parent:
            attachment["parentItem"] = parent["key"]
            attachment.pop("collections", None)
        else:
            attachment["collections"] = [collection_key]
        item = client.create("items", attachment, entry["attachment_write_token"])
        entry["attachment_created"] = True
        save("attachment_created")
    parent_key = item["data"].get("parentItem")
    if parent_key:
        parent = client.get("items", parent_key)
        if not parent:
            raise WebError("Attachment parent is unavailable")
        if metadata and any(parent["data"].get(field) != value for field, value in metadata["data"].items()):
            raise WebError("Remote bibliographic metadata differs from the reviewed input; reconcile before reuse")
        ensure_membership(client, parent, collection_key, wanted_tags)
    item = ensure_membership(client, item, collection_key, wanted_tags | {content_tag}, child=bool(parent_key))
    client.upload(item, path, details, save)
    verified = client.get("items", item["key"])
    if not verified or verified["data"].get("md5") != details["md5"] or verified["data"].get("contentType") != "application/pdf":
        raise WebError("Registered attachment metadata/hash verification failed")
    if not (wanted_tags | {content_tag}) <= tags(verified) or (verified["data"].get("parentItem") or None) != (parent_key or None) or (not parent_key and collection_key not in verified["data"].get("collections", [])):
        raise WebError("Final remote membership verification failed")
    if parent_key:
        final_parent = client.get("items", parent_key)
        if not final_parent or not wanted_tags <= tags(final_parent) or collection_key not in final_parent["data"].get("collections", []):
            raise WebError("Final parent collection/tag verification failed")
    if fingerprint(path)["sha256"] != details["sha256"]:
        raise WebError("Local PDF changed during verification; reconcile the archived version")
    entry.update(status="imported", imported_at=utc(), metadata_status="reviewed_input_verified" if metadata else "pending")
    save("import_verified")
    return {"sha256": details["sha256"], "attachment_key": item["key"], "parent_key": parent_key,
            "status": "reused" if entry.get("reused") else "imported", "pdf_validation": details,
            "metadata_status": entry["metadata_status"], "remote_md5_verified": True}


def finalize_result(result, write):
    resolved = {item.get("sha256") for item in result["imported"] + result["failed"]}
    result["unresolved"] = [{"sha256": item["sha256"], "status": "not_processed"} for item in result["planned"] if write and item["sha256"] not in resolved]
    result["counts"] = {name: len(result[name]) for name in ("planned", "imported", "skipped", "failed", "unresolved")}
    result["counts"]["metadata_pending"] = sum(item["metadata_status"] == "pending" for item in result["imported"])
    result["counts"]["reused"] = sum(item["status"] == "reused" for item in result["imported"])
    result["cloud_verification"] = "completed_for_imported_files" if write and result["imported"] else "not_performed"
    result["limitations"] = ["No automatic PDF bibliographic recognition via this adapter; missing metadata remains pending.", "File verification reads back registered MD5/content type and membership; it is not a visual/scientific review."]


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--source", type=Path, help="Selected PDF or directory (inside the workspace)")
    result.add_argument("--library-type", choices=("user", "group"), default=os.environ.get("ZOTERO_LIBRARY_TYPE", "user"))
    result.add_argument("--library-id", default=os.environ.get("ZOTERO_LIBRARY_ID", ""))
    result.add_argument("--api-key-env", default="ZOTERO_API_KEY")
    result.add_argument("--api-key-file", type=Path, help="Private key file; its contents are never recorded")
    result.add_argument("--batch-id", help="YYYYMMDDHHmm; reused when resuming this batch")
    result.add_argument("--collection-key", help="Existing collection; otherwise create/reuse a timestamp collection")
    result.add_argument("--parent-collection", help="Optional parent for the timestamp collection")
    result.add_argument("--collection-prefix", default="BoomSkills")
    result.add_argument("--tag", action="append", default=[])
    result.add_argument("--metadata", type=Path, help="Reviewed metadata JSON; see references/web-api.md")
    result.add_argument("--manifest", type=Path, help="Private persistent state for deduplication/recovery")
    result.add_argument("--out", type=Path, help="New directory for this attempt's JSON result and Markdown report")
    result.add_argument("--recursive", action=argparse.BooleanOptionalAction, default=True)
    result.add_argument("--timeout", type=float, default=60)
    result.add_argument("--yes", action="store_true", help="Write metadata/collections and upload selected PDFs to the cloud")
    result.add_argument("--dry-run", action="store_true", help="Offline PDF validation and plan; no cloud requests/writes")
    result.add_argument("--check", action="store_true", help="Only verify authenticated cloud read access; no import")
    result.add_argument("--stop-on-error", action="store_true")
    return result


def run(args, *, client_factory=Client):
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", args.api_key_env):
        raise WebError("API key environment variable name must be uppercase")
    if args.collection_key and args.parent_collection:
        raise WebError("Choose --collection-key or --parent-collection, not both")
    for key in (args.collection_key, args.parent_collection):
        if key and not valid_key(key):
            raise WebError("Collection keys must be valid eight-character Zotero keys")
    library = {"type": args.library_type, "id": str(args.library_id)}
    if library["type"] not in {"user", "group"} or not library["id"].isdigit() or int(library["id"]) < 1:
        raise WebError("Set the numeric library ID from Zotero API Keys settings (not a username)")
    write = args.yes and not args.dry_run and not args.check
    client = None
    if write or args.check:
        secret = args.api_key_file.read_text(encoding="utf-8").strip() if args.api_key_file else os.environ.get(args.api_key_env, "").strip()
        client = client_factory(library["type"], library["id"], secret, timeout=args.timeout)
    if args.check:
        client.request("GET", client.prefix + "/collections?limit=1")
        return {"mode": "check", "library_type": library["type"], "read_access": "verified",
                "write_access": "unverified_until_write", "file_upload_access": "unverified_until_upload"}, 0
    if not args.source:
        raise WebError("Supply --source for an import or --check for a connection probe")
    source = args.source.resolve()
    if not source.exists() or (source.is_file() and source.suffix.lower() != ".pdf"):
        raise WebError("Source must be a selected PDF or directory")
    source_dir = source if source.is_dir() else source.parent
    files = sorted((p for p in source_dir.rglob("*") if p.suffix.lower() == ".pdf" and p.is_file()), key=lambda p: p.as_posix()) if source.is_dir() and args.recursive else sorted(source.glob("*.[pP][dD][fF]")) if source.is_dir() else [source]
    if not files:
        raise WebError("No PDFs selected")
    metadata = load_metadata(args.metadata, source_dir)
    if set(metadata) - {p.resolve() for p in files}:
        raise WebError("Metadata includes files outside the selected PDF set")
    batch_id = args.batch_id or datetime.now().strftime("%Y%m%d%H%M")
    if not re.fullmatch(r"\d{12}", batch_id):
        raise WebError("Batch ID must use YYYYMMDDHHmm")
    datetime.strptime(batch_id, "%Y%m%d%H%M")
    manifest_path = args.manifest or source_dir / ".boomskills" / "zotero-web-manifest.json"
    attempt_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:10]
    output = args.out or (manifest_path.parent / "batches" / attempt_id if write else None)
    if output:
        # Ensure reports can be saved before doing any cloud mutation.
        output.mkdir(parents=True, exist_ok=False)
    result = {"adapter": "web_api_v3", "attempt_id": attempt_id, "batch_id": batch_id, "batch_tag": f"batch:{batch_id}",
              "dry_run": not write, "library_type": library["type"], "imported": [], "skipped": [], "failed": [], "planned": []}
    prepared = []
    seen = set()
    for index, path in enumerate(files):
        try:
            details = fingerprint(path)
            if details["sha256"] in seen:
                result["skipped"].append({"sha256": details["sha256"], "reason": "duplicate_in_selection"})
                continue
            seen.add(details["sha256"])
            paper_metadata = metadata.get(path.resolve())
            prepared.append((path, details, paper_metadata))
            result["planned"].append({"sha256": details["sha256"], "pages": details["pages"], "metadata_status": "reviewed_input" if paper_metadata else "pending"})
        except Exception as exc:
            # Parser exceptions can embed local paths. Keep a neutral locator and exception type.
            result["failed"].append({"input_index": index, "status": "invalid_pdf", "error": str(exc) if isinstance(exc, WebError) else "PDF validation failed (" + type(exc).__name__ + ")"})
    if write:
        with manifest_lock(manifest_path):
            manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"version": 1, "adapter": "web_api_v3", "library": library, "files": {}, "batches": {}, "attempts": []}
            if manifest.get("version") != 1 or manifest.get("adapter") != "web_api_v3" or manifest.get("library") != library:
                raise WebError("Manifest belongs to another adapter/library or unsupported version")
            policy = {"collection_name": args.collection_prefix + " " + batch_id, "requested_key": args.collection_key, "parent": args.parent_collection}
            batches = manifest["batches"]
            batch = batches.setdefault(batch_id, {**policy, "write_token": uuid.uuid4().hex})
            if any(batch.get(k) != v for k, v in policy.items()):
                raise WebError("Batch collection policy changed; resume with the original arguments or use a new batch")
            attempt = {"id": attempt_id, "batch_id": batch_id, "started_at": utc(), "status": "running", "events": []}
            manifest["attempts"].append(attempt)

            def checkpoint(stage, sha=None):
                attempt["events"].append({"stage": stage, "sha256": sha, "at": utc()})
                atomic_json(manifest_path, manifest)

            checkpoint("attempt_started")
            try:
                if prepared:
                    collection_key = collection(client, batch, args, checkpoint)
                    result["collection_key"] = collection_key
                    wanted_tags = {result["batch_tag"], *args.tag}
                    for path, details, paper_metadata in prepared:
                        sha = details["sha256"]
                        entry = manifest["files"].setdefault(sha, {"sha256": sha, "metadata_hash": metadata_hash(paper_metadata), "status": "prepared"})
                        try:
                            if entry["metadata_hash"] != metadata_hash(paper_metadata):
                                raise WebError("Reviewed metadata changed since the first attempt; reconcile it explicitly")
                            paper_result = import_pdf(client, path, details, paper_metadata, entry, collection_key, wanted_tags,
                                                lambda stage: checkpoint(stage, sha))
                            result["imported"].append(paper_result)
                        except (WebError, OSError, ValueError, KeyError) as exc:
                            entry["status"] = "partial" if entry.get("attachment_key") or entry.get("parent_key") else "failed"
                            failure = {"sha256": sha, "status": entry["status"], "error": str(exc) if isinstance(exc, WebError) else "Import failed (" + type(exc).__name__ + ")",
                                       "attachment_key": entry.get("attachment_key"), "parent_key": entry.get("parent_key")}
                            if isinstance(exc, WebError) and exc.retry_after:
                                failure["retry_after_seconds"] = exc.retry_after
                            result["failed"].append(failure)
                            checkpoint("import_failed", sha)
                            if args.stop_on_error:
                                break
            except WebError as exc:
                result["failed"].append({"status": "batch_failed", "error": str(exc), "retry_after_seconds": exc.retry_after})
            finally:
                finalize_result(result, write)
                attempt.update(status="failed" if result["failed"] else "verified", finished_at=utc(), result=result)
                checkpoint("attempt_finished")
    finalize_result(result, write)
    if output:
        atomic_json(output / "import-result.json", result)
        rows = ["# Zotero cloud import report", "", f"Batch: `{batch_id}`; adapter: Web API v3; dry run: {not write}.", "",
                f"Planned: {len(prepared)}; verified imports: {len(result['imported'])}; duplicates skipped: {len(result['skipped'])}; failures: {len(result['failed'])}.", "",
                f"Not processed: {result['counts']['unresolved']}; metadata pending: {result['counts']['metadata_pending']}; reused cloud attachments: {result['counts']['reused']}.", "",
                "## Verification", "", "Registered remote hashes, PDF content type, collection membership and batch tags are checked for each verified import. Offline plans have no cloud verification.", "",
                "## Metadata and limits", "", "Bibliographic metadata is verified against explicitly reviewed input when supplied. Entries without it remain metadata-pending. No desktop PDF recognition is invoked.", "",
                "## Recovery", "", "Reuse the same private manifest and batch ID. Saved object keys and cloud content tags are reconciled before continuing; prior attempt events remain preserved. Resolve permissions, storage quota or conflicts before retrying.", "",
                "See import-result.json for actual per-file states and failures."]
        (output / "import-report.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
        result["output_directory"] = output.name
    return result, 1 if result["failed"] else 0


def main():
    args = parser().parse_args()
    try:
        result, code = run(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return code
    except (WebError, OSError, ValueError, KeyError, ImportError) as exc:
        detail = str(exc) if isinstance(exc, WebError) else "Configuration/input error (" + type(exc).__name__ + "); check dependencies and the private manifest"
        print(json.dumps({"error": detail, "next": "Read references/web-api.md; keep the same manifest when recovering"}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
