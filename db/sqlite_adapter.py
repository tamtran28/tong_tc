import importlib.util


def _load_sqlite_module():
    if importlib.util.find_spec("sqlite3"):
        import sqlite3
        return sqlite3

    import pysqlite3
    return pysqlite3


sqlite3 = _load_sqlite_module()
__all__ = ["sqlite3"]
