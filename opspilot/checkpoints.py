"""Manage PostgreSQL LangGraph savers and serialize writes to each thread."""

from contextlib import contextmanager
from time import sleep


@contextmanager
def checkpoint_saver(dsn: str, lock_key: str, *, schema_setup: bool = False):
    from langgraph.checkpoint.postgres import PostgresSaver
    from psycopg import connect
    from psycopg.rows import dict_row

    with connect(
        dsn,
        autocommit=True,
        prepare_threshold=0,
        row_factory=dict_row,
        connect_timeout=5,
    ) as connection:
        # The session lock is automatically released when the connection closes.
        if schema_setup:
            # Concurrent index creation waits for open transactions, including
            # sessions blocked on a lock. Each try ends its transaction promptly.
            while not connection.execute(
                "SELECT pg_try_advisory_lock(hashtextextended(%s, 0)) AS acquired",
                (lock_key,),
            ).fetchone()["acquired"]:
                sleep(0.1)
        else:
            connection.execute(
                "SELECT pg_advisory_lock(hashtextextended(%s, 0))", (lock_key,)
            )
        yield PostgresSaver(connection)


def setup_checkpoints(dsn: str) -> None:
    with checkpoint_saver(
        dsn, "opspilot:checkpoint-schema", schema_setup=True
    ) as saver:
        saver.setup()
