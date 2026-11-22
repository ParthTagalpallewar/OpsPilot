"""Database connections for the single-node and shared investigation stores."""

import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path


class PostgresConnection:
    def __init__(self, connection):
        self.connection = connection

    def execute(self, query: str, parameters=()):
        return self.connection.execute(query.replace("?", "%s"), parameters)


class InvestigationDatabase:
    def __init__(self, target: Path | str):
        self.target = target
        self.postgres = isinstance(target, str)
        self.job_order = "enqueue_order" if self.postgres else "rowid"

    @contextmanager
    def session(self, *, write: bool = False):
        if self.postgres:
            try:
                import psycopg
            except ImportError as exc:
                raise ValueError(
                    "PostgreSQL requires uv sync --extra postgres"
                ) from exc

            with psycopg.connect(self.target, connect_timeout=5) as raw:
                connection = PostgresConnection(raw)
                if write:
                    # Serialize short state transitions. Replay runs outside the lock.
                    connection.execute("SELECT pg_advisory_xact_lock(530411699)")
                else:
                    connection.execute(
                        "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"
                    )
                yield connection
        else:
            with closing(sqlite3.connect(self.target)) as connection, connection:
                connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
                yield connection
