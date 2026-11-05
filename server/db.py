import os
from pathlib import Path

from psycopg_pool import ConnectionPool

_pool = None


def database_url():
    return os.environ.get("DATABASE_URL", "postgresql://ipetro:ipetro@localhost:5432/ipetro")


def pool():
    global _pool
    if _pool is None:
        _pool = ConnectionPool(database_url(), min_size=1, max_size=int(os.environ.get("DB_POOL", "10")), open=True)
    return _pool


def close():
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def init_schema():
    sql = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")
    with pool().connection() as c:
        c.execute(sql)
