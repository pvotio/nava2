import logging
from typing import Any

from .templates_repo import registry

logger = logging.getLogger(__name__)


class ValidationError(ValueError):
    pass


class Validator:
    def __init__(self, template_id: str, args: dict[str, Any] | None):
        self.template_id = template_id
        self.args = args or {}

    def validate(self) -> tuple[str, dict[str, Any]]:
        tmpl = registry.get_template(self.template_id)
        if not tmpl:
            registry.sync_index()
            tmpl = registry.get_template(self.template_id)
            if not tmpl:
                raise ValidationError(f"Unknown template_id: {self.template_id}")

        schema = tmpl.get("args") or {}
        required = set(schema.get("required") or [])
        optional = set(schema.get("optional") or [])
        defaults = schema.get("defaults") or {}

        missing = [k for k in required if k not in self.args]
        if missing:
            raise ValidationError(f"Missing required args: {missing}")

        allowed = required | optional
        process_args: dict[str, Any] = {k: v for k, v in self.args.items() if k in allowed}
        for k, v in defaults.items():
            process_args.setdefault(k, v)

        module_name = tmpl.get("module") or "generic"
        logger.debug(
            "Validated template '%s' with module '%s' and args %s",
            self.template_id,
            module_name,
            list(process_args.keys()),
        )
        return module_name, process_args
