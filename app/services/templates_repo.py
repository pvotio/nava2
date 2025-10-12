import hashlib
import json
import logging
from urllib.parse import urljoin

import httpx

from ..core.config import settings
from ..db.redis_client import redis_client

logger = logging.getLogger(__name__)

INDEX_KEY = "templates:index"
INDEX_ETAG_KEY = "templates:etag"


def _parent_url(url: str) -> str:
    parts = url.rsplit("/", 1)
    return parts[0] + "/" if len(parts) == 2 else url


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class TemplateRegistry:
    def __init__(self):
        self.r = redis_client
        self.base_url = _parent_url(settings.TEMPLATES_INDEX_URL)

    def _auth_headers(self) -> dict:
        h = {"Accept": "application/json", "Cache-Control": "no-cache"}
        if settings.GITHUB_TOKEN:
            h["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
        return h

    def _text_headers(self) -> dict:
        h = {"Accept": "*/*", "Cache-Control": "no-cache"}
        if settings.GITHUB_TOKEN:
            h["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
        return h

    def fetch_remote_index_text(self, force: bool = False) -> str:
        url = settings.TEMPLATES_INDEX_URL
        if force:
            # cache-bust when forced
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}cb={hashlib.sha1().hexdigest()}"
        resp = httpx.get(url, headers=self._auth_headers(), timeout=30)
        resp.raise_for_status()
        return resp.text

    def sync_index(self, force: bool = False) -> dict:
        text = self.fetch_remote_index_text(force=force)
        data = json.loads(text)
        etag = _sha256_hex(text)

        old = self.r.get(INDEX_ETAG_KEY)
        if force or old != etag:
            self.r.set(INDEX_KEY, text)
            self.r.set(INDEX_ETAG_KEY, etag)
            logger.info("Templates index updated (etag=%s)", etag[:12])
        else:
            logger.debug("Templates index unchanged (etag=%s)", etag[:12])
        return data

    def get_index(self) -> dict:
        raw = self.r.get(INDEX_KEY)
        if not raw:
            logger.info("Templates index missing in Redis; syncing")
            return self.sync_index(force=True)
        return json.loads(raw)

    def list_templates(self) -> list[dict]:
        return self.get_index().get("templates", [])

    def get_template(self, template_id: str) -> dict | None:
        return next((t for t in self.list_templates() if t.get("id") == template_id), None)

    def _resolve_file_url(self, template: dict, filename: str, force: bool = False) -> str:
        rel = f"{template['path'].rstrip('/')}/{filename.lstrip('/')}"
        url = urljoin(self.base_url, rel)
        return url

    def _keys(self, tid: str) -> dict:
        base = f"template:{tid}"
        return {
            "meta": f"{base}:meta",
            "html": f"{base}:html",
            "logic": f"{base}:logic",
            "test": f"{base}:test",
            "etag": f"{base}:etag",
        }

    def _template_etag(self, template: dict) -> str:
        return _sha256_hex(json.dumps(template, sort_keys=True))

    def fetch_and_cache_assets(self, template: dict, force: bool = False) -> None:
        tid = template["id"]
        files = template.get("files", {})
        keys = self._keys(tid)
        new_etag = self._template_etag(template)
        old_etag = self.r.get(keys["etag"])

        if (
            not force
            and old_etag == new_etag
            and all(self.r.exists(keys[k]) for k in ("html", "logic", "test"))
        ):
            logger.debug("Template %s assets unchanged", tid)
            return

        html_url = self._resolve_file_url(template, files.get("html", "template.html"), force=force)
        logic_url = self._resolve_file_url(template, files.get("logic", "logic.py"), force=force)
        test_url = self._resolve_file_url(template, files.get("test", "test.py"), force=force)

        logger.debug(f"URLTEST {html_url}")
        logger.debug(f"URLTEST {logic_url}")
        logger.debug(f"URLTEST {test_url}")

        html_resp = httpx.get(html_url, headers=self._text_headers(), timeout=30)
        html_resp.raise_for_status()
        logic_resp = httpx.get(logic_url, headers=self._text_headers(), timeout=30)
        logic_resp.raise_for_status()
        test_resp = httpx.get(test_url, headers=self._text_headers(), timeout=30)
        test_resp.raise_for_status()

        self.r.set(keys["meta"], json.dumps(template))
        self.r.set(keys["html"], html_resp.text)
        self.r.set(keys["logic"], logic_resp.text)
        self.r.set(keys["test"], test_resp.text)
        self.r.set(keys["etag"], new_etag)

        logger.info("Cached assets for template %s (etag=%s)", tid, new_etag[:12])

    def sync_all_assets(self, force: bool = False) -> int:
        idx = self.get_index()
        count = 0
        for t in idx.get("templates", []):
            try:
                self.fetch_and_cache_assets(t, force=force)
                count += 1
            except Exception as e:
                logger.error("Failed caching assets for %s: %s", t.get("id"), e)
        return count

    def get_cached_assets(self, template_id: str) -> dict | None:
        keys = self._keys(template_id)
        meta = self.r.get(keys["meta"])
        html = self.r.get(keys["html"])
        logic = self.r.get(keys["logic"])
        test = self.r.get(keys["test"])
        if not (meta and html and logic and test):
            return None
        return {"meta": json.loads(meta), "html": html, "logic": logic, "test": test}


registry = TemplateRegistry()
