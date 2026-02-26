import re

from django.db.backends.oracle.base import DatabaseWrapper as OracleDatabaseWrapper

from .schema import DatabaseSchemaEditor


def _rewrite_fetch_first(sql):
    """Rewrite FETCH FIRST N ROWS ONLY to Oracle 11g ROWNUM syntax.

    Oracle 11g does not support the FETCH FIRST clause. This function
    converts it into a ROWNUM-based subquery that preserves ORDER BY
    semantics.
    """
    if not isinstance(sql, str):
        return sql

    match = re.search(r"FETCH FIRST (\d+) ROWS ONLY", sql, re.IGNORECASE)
    if not match:
        return sql

    limit = match.group(1)
    sql = sql[: match.start()].rstrip() + sql[match.end() :]

    # Check for ORDER BY – if present, we need to wrap in a subquery so
    # ROWNUM is applied *after* sorting.
    order_match = re.search(r"\bORDER\s+BY\b", sql, re.IGNORECASE)
    if order_match:
        sql = (
            f"SELECT * FROM ({sql}) WHERE ROWNUM <= {limit}"
        )
    else:
        # Simple case: inject ROWNUM into the existing WHERE (or add one).
        if re.search(r"\bWHERE\b", sql, re.IGNORECASE):
            sql = re.sub(
                r"\bWHERE\b",
                f"WHERE ROWNUM <= {limit} AND",
                sql,
                count=1,
                flags=re.IGNORECASE,
            )
        else:
            from_match = re.search(r"\bFROM\s+([\w\".]+)", sql, re.IGNORECASE)
            if from_match:
                end = from_match.end()
                sql = sql[:end] + f" WHERE ROWNUM <= {limit}" + sql[end:]

    return sql


class OracleCursorWrapper:
    """Thin cursor wrapper that rewrites SQL for Oracle 11g compatibility."""

    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, sql, params=None):
        sql = _rewrite_fetch_first(sql)
        if params is None:
            return self.cursor.execute(sql)
        return self.cursor.execute(sql, params)

    def executemany(self, sql, param_list):
        sql = _rewrite_fetch_first(sql)
        return self.cursor.executemany(sql, param_list)

    def __getattr__(self, attr):
        return getattr(self.cursor, attr)

    def __iter__(self):
        return iter(self.cursor)


class DatabaseWrapper(OracleDatabaseWrapper):
    SchemaEditorClass = DatabaseSchemaEditor

    data_types = OracleDatabaseWrapper.data_types.copy()
    data_types["AutoField"] = "NUMBER(11)"
    data_types["BigAutoField"] = "NUMBER(19)"
    data_types["SmallAutoField"] = "NUMBER(5)"

    def check_database_version_supported(self):
        return

    def create_cursor(self, name=None):
        cursor = super().create_cursor(name=name)
        return OracleCursorWrapper(cursor)
