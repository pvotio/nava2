class TemplateNotFoundError(Exception):
    pass


class LogicExecutionError(Exception):
    pass


class TestExecutionError(Exception):
    pass


class NoDataFoundError(Exception):
    """For when 'test.py' check fails (record not found / args invalid)."""
