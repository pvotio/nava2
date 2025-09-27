from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from jinja2 import BaseLoader, Environment

from .exceptions import (
    LogicExecutionError,
    NoDataFoundError,
    TemplateNotFoundError,
    TestExecutionError,
)

# from .mssql import MSSQLClient
from .runtime import exec_module, require_callable
from .templates_repo import registry

logger = logging.getLogger(__name__)


def _ensure_assets(template_id: str) -> dict:
    assets = registry.get_cached_assets(template_id)
    if assets:
        return assets
    tmpl = registry.get_template(template_id)
    if not tmpl:
        registry.sync_index()
        tmpl = registry.get_template(template_id)
        if not tmpl:
            raise TemplateNotFoundError(f"Unknown template_id: {template_id}")
    registry.fetch_and_cache_assets(tmpl, force=True)
    assets = registry.get_cached_assets(template_id)
    if not assets:
        raise TemplateNotFoundError(f"Assets not cached for template_id: {template_id}")
    return assets


# def _with_mssql() -> MSSQLClient:
#     return MSSQLClient()


def fetch_placeholders(template_id: str, process_args: dict[str, Any]) -> dict[str, Any]:
    assets = _ensure_assets(template_id)
    test_src = assets["test"]
    logic_src = assets["logic"]
    try:
        ns_test = exec_module(test_src)
        if hasattr(ns_test, "main"):
            # with _with_mssql() as db:
            ok = require_callable(ns_test, "main")(process_args, False)
            if not bool(ok):
                raise NoDataFoundError(
                    "No data found or preconditions failed (test.main returned False)."
                )

    except AttributeError:
        pass
    except Exception as err:
        raise TestExecutionError(str(err)) from err

    try:
        ns = exec_module(logic_src)
        # with _with_mssql() as db:
        placeholders = require_callable(ns, "main")(process_args, False)
        if not isinstance(placeholders, dict):
            raise LogicExecutionError("logic.main() must return a dict of placeholders")
        return placeholders
    except Exception as err:
        raise LogicExecutionError(str(err)) from err


def render_html(template_id: str, placeholders: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    assets = _ensure_assets(template_id)
    html_tpl = assets["html"]

    meta = assets.get("meta", {})
    pdf_opts = (meta.get("pdf") or {}) if isinstance(meta, dict) else {}
    kwargs = {
        "page_size": pdf_opts.get("page_size", "A4"),
        "orientation": pdf_opts.get("orientation", "L"),
        "header": pdf_opts.get("header", "<div style='font-size:12px'>Header</div>"),
        "footer": pdf_opts.get("footer", "<div style='font-size:12px'>Footer</div>"),
    }

    env = Environment(loader=BaseLoader(), autoescape=False)
    tmpl = env.from_string(html_tpl)
    ctx = dict(placeholders)
    ctx.setdefault("generated_at", datetime.now(UTC).isoformat())
    rendered = tmpl.render(**ctx)
    return rendered, kwargs
