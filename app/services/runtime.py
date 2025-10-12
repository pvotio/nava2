from __future__ import annotations

import json
import math
import os
import re
from datetime import datetime, timezone
from types import SimpleNamespace

SAFE_GLOBALS = {
    "__name__": "__template_script__",
    "datetime": datetime,
    "timezone": timezone,
    "json": json,
    "math": math,
    "os": os,
    "re": re,
}


def exec_module(source: str) -> SimpleNamespace:
    env: dict = dict(SAFE_GLOBALS)
    exec(source, env, env)
    return SimpleNamespace(**env)


def require_callable(ns: SimpleNamespace, name: str):
    fn = getattr(ns, name, None)
    if not callable(fn):
        raise AttributeError(f"Function {name!r} not found in script")
    return fn
