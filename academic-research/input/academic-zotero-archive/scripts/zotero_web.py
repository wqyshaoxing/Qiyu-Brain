#!/usr/bin/env python3
"""Small Zotero Web API v3 client. Credentials never travel to file storage."""
from __future__ import annotations

import hashlib
import json
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.zotero.org"
KEY_ALPHABET = "23456789ABCDEFGHIJKLMNPQRSTUVWXYZ"


class WebError(RuntimeError):
    def __init__(self, message, status=None, retry_after=None):
        super().__init__(message)
        self.status = status
        self.retry_after = retry_after


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def object_key():
    return "".join(secrets.choice(KEY_ALPHABET) for _ in range(8))


def valid_key(key):
    return isinstance(key, str) and len(key) == 8 and all(c in KEY_ALPHABET for c in key)


def transport(method, url, headers, body, timeout):
    """Do not follow redirects with API credentials or signed upload bodies."""
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    opener = urllib.request.build_opener(NoRedirect())
    try:
        with opener.open(request, timeout=timeout) as response:
            raw = response.read(8 * 1024 * 1024 + 1)
            if len(raw) > 8 * 1024 * 1024:
                raise WebError("API response exceeds the response-size limit")
            return response.status, dict(response.headers), raw
    except urllib.error.HTTPError as exc:
        # Server bodies and upload URLs may contain private information.
        return exc.code, dict(exc.headers), b""
    except (urllib.error.URLError, OSError) as exc:
        raise WebError("Network failure; retain the manifest and reconcile before retrying") from exc


def header(headers, name, default=None):
    return next((value for key, value in headers.items() if key.lower() == name.lower()), default)


class Client:
    def __init__(self, library_type, library_id, api_key, *, timeout=60, send=transport, sleep=time.sleep, now=time.monotonic):
        if library_type not in {"user", "group"} or not str(library_id).isdigit() or int(library_id) < 1:
            raise WebError("Configure library_type=user/group and a positive numeric library_id")
        if not api_key or any(ord(c) < 33 or ord(c) > 126 for c in api_key):
            raise WebError("Set the configured API key environment variable or supply a private key file")
        if timeout <= 0:
            raise WebError("Request timeout must be positive")
        self.prefix = f"/{'users' if library_type == 'user' else 'groups'}/{library_id}"
        self.api_key, self.timeout = api_key, timeout
        self.send, self.sleep, self.now = send, sleep, now
        self.not_before = 0.0

    def request(self, method, path, *, payload=None, headers=None, accepted=(200,)):
        if not path.startswith("/") or path.startswith("//"):
            raise WebError("Invalid API-relative path")
        outgoing = {"Zotero-API-Version": "3", "Zotero-API-Key": self.api_key, "Accept": "application/json"}
        outgoing.update(headers or {})
        if isinstance(payload, (dict, list)):
            payload = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            outgoing["Content-Type"] = "application/json"
        for attempt in range(3):
            wait = max(0, self.not_before - self.now())
            if wait > 30:
                raise WebError("Server requested a longer backoff; retry later with the same manifest", retry_after=round(wait))
            if wait:
                self.sleep(wait)
            status, received, raw = self.send(method, API + path, outgoing, payload, self.timeout)
            try:
                delay = max(0, float(header(received, "Backoff", 0)), float(header(received, "Retry-After", 0)))
            except (ValueError, TypeError):
                delay = 30
            self.not_before = self.now() + delay
            # Only reads are retried automatically. Writes are reconciled by saved keys.
            if method == "GET" and (status == 429 or status in {500, 502, 503, 504}) and attempt < 2:
                self.not_before = max(self.not_before, self.now() + 2 ** attempt)
                continue
            if status not in accepted:
                hints = {403: "API key or library/file-edit permission denied", 409: "library locked", 412: "version/file conflict; reconcile remote state", 413: "Zotero Storage quota exceeded", 429: "rate limited; retry after the indicated delay"}
                raise WebError(f"Zotero HTTP {status}: {hints.get(status, 'request rejected; reconcile before retrying')}", status, delay or None)
            if not raw:
                return None, received
            try:
                return json.loads(raw.decode("utf-8")), received
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise WebError("API returned invalid JSON") from exc
        raise WebError("Read retry limit reached")

    def get(self, resource, key):
        if not valid_key(key):
            raise WebError("Invalid Zotero object key")
        value, _ = self.request("GET", self.prefix + f"/{resource}/{key}", accepted=(200, 404))
        return value

    def pages(self, resource, **query):
        start = 0
        result = []
        while True:
            params = {**query, "format": "json", "limit": 100, "start": start}
            value, headers = self.request("GET", self.prefix + "/" + resource + "?" + urllib.parse.urlencode(params))
            if not isinstance(value, list):
                raise WebError("Expected a paginated object list")
            result.extend(value)
            start += len(value)
            total = header(headers, "Total-Results")
            if len(value) < 100 or (total is not None and start >= int(total)):
                return result
            if start > 100000:
                raise WebError("Pagination limit reached; narrow the requested library scope")

    def create(self, resource, data, write_token):
        value, _ = self.request("POST", self.prefix + "/" + resource, payload=[data], headers={"Zotero-Write-Token": write_token})
        if not isinstance(value, dict) or value.get("failed"):
            raise WebError("Object write was rejected inside the HTTP 200 response; inspect metadata and permissions")
        saved = value.get("successful", {}).get("0")
        if saved:
            if saved.get("key") != data["key"]:
                raise WebError("Object write returned an unexpected key")
            return saved
        if value.get("unchanged", {}).get("0") == data["key"]:
            return self.get(resource, data["key"])
        raise WebError("Object write has no successful result")

    def patch(self, item, fields):
        version = item.get("version", item.get("data", {}).get("version"))
        if not isinstance(version, int):
            raise WebError("Remote item lacks its current version")
        self.request("PATCH", self.prefix + "/items/" + item["key"], payload=fields,
                     headers={"If-Unmodified-Since-Version": str(version)}, accepted=(204,))

    def template(self, item_type, link_mode=None):
        query = {"itemType": item_type}
        if link_mode:
            query["linkMode"] = link_mode
        value, _ = self.request("GET", "/items/new?" + urllib.parse.urlencode(query))
        if not isinstance(value, dict) or value.get("itemType") != item_type:
            raise WebError("Invalid Zotero item template")
        return value

    def upload(self, item, path: Path, fingerprint, checkpoint):
        """Authorize, upload, register, and read back the file's server MD5."""
        data = item["data"]
        previous = data.get("md5")
        if previous:
            if previous != fingerprint["md5"]:
                raise WebError("Remote attachment has different content; it will not be overwritten")
            checkpoint("file_already_registered")
            return
        # Check the exact bytes used for the upload, after earlier metadata writes.
        blob = path.read_bytes()
        if hashlib.sha256(blob).hexdigest() != fingerprint["sha256"]:
            raise WebError("Source PDF changed during import; restore it and reconcile the saved item")
        form = {"md5": fingerprint["md5"], "filename": data["filename"], "filesize": len(blob), "mtime": fingerprint["mtime"]}
        endpoint = self.prefix + "/items/" + item["key"] + "/file"
        content_type = {"Content-Type": "application/x-www-form-urlencoded", "If-None-Match": "*"}
        authorization, _ = self.request("POST", endpoint, payload=urllib.parse.urlencode(form).encode(), headers=content_type)
        if not isinstance(authorization, dict):
            raise WebError("Invalid upload authorization response")
        if authorization.get("exists") == 1:
            checkpoint("file_associated_from_storage")
            return
        required = {"url", "contentType", "prefix", "suffix", "uploadKey"}
        if not required <= authorization.keys() or not all(isinstance(authorization[k], str) for k in required):
            raise WebError("Incomplete upload authorization")
        parsed = urllib.parse.urlsplit(authorization["url"])
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise WebError("Upload authorization requires a credential-free HTTPS destination")
        if any(c in authorization["contentType"] for c in "\r\n"):
            raise WebError("Invalid storage Content-Type")
        checkpoint("upload_authorized")  # Upload keys and signed URLs are deliberately not persisted.
        body = authorization["prefix"].encode() + blob + authorization["suffix"].encode()
        # Separate storage request: no Zotero-API-Key, no Authorization, no automatic redirects.
        status, _, _ = self.send("POST", authorization["url"], {"Content-Type": authorization["contentType"]}, body, self.timeout)
        if status != 201:
            raise WebError(f"File-storage upload failed (HTTP {status}); resume using the saved attachment key", status)
        checkpoint("storage_uploaded")
        self.request("POST", endpoint, payload=urllib.parse.urlencode({"upload": authorization["uploadKey"]}).encode(), headers=content_type, accepted=(204,))
        checkpoint("upload_registered")
