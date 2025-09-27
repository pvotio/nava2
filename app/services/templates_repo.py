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


class TemplateRegistry:
    def __init__(self):
        self.r = redis_client
        self.base_url = _parent_url(settings.TEMPLATES_INDEX_URL)

    def _auth_headers(self) -> dict:
        h = {"Accept": "application/json"}
        if settings.GITHUB_TOKEN:
            h["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
        return h

    def _text_headers(self) -> dict:
        h = {"Accept": "*/*"}
        if settings.GITHUB_TOKEN:
            h["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
        return h

    def fetch_remote_index(self) -> dict:
        resp = httpx.get(settings.TEMPLATES_INDEX_URL, headers=self._auth_headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()

    def sync_index(self) -> dict:
        data = self.fetch_remote_index()
        etag = json.dumps(data.get("version") or data.get("commit") or data.get("templates", []))[
            :64
        ]
        old = self.r.get(INDEX_ETAG_KEY)
        if old != etag:
            self.r.set(INDEX_KEY, json.dumps(data))
            self.r.set(INDEX_ETAG_KEY, etag)
            logger.info("Templates index updated (etag=%s)", etag)
        else:
            logger.debug("Templates index unchanged")
        return data

    def get_index(self) -> dict:
        raw = self.r.get(INDEX_KEY)
        if not raw:
            logger.info("Templates index missing in Redis; syncing")
            return self.sync_index()
        return json.loads(raw)

    def list_templates(self) -> list[dict]:
        return self.get_index().get("templates", [])

    def get_template(self, template_id: str) -> dict | None:
        return next((t for t in self.list_templates() if t.get("id") == template_id), None)

    def _resolve_file_url(self, template: dict, filename: str) -> str:
        rel = f"{template['path'].rstrip('/')}/{filename.lstrip('/')}"
        return urljoin(self.base_url, rel)

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
        return json.dumps(
            {
                "id": template.get("id"),
                "files": template.get("files"),
                "version": template.get("version") or template.get("updated_at") or "",
            },
            sort_keys=True,
        )[:128]

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

        html_url = self._resolve_file_url(template, files.get("html", "template.html"))
        logic_url = self._resolve_file_url(template, files.get("logic", "logic.py"))
        test_url = self._resolve_file_url(template, files.get("test", "test.py"))

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

        logger.info("Cached assets for template %s", tid)

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
