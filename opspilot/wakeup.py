"""Optional Redis wake-up hints for the database-backed queue."""

import os
from time import sleep

DEFAULT_KEY = "opspilot:replay:wakeup"


class WorkerWakeup:
    def __init__(self, url: str | None = None, key: str = DEFAULT_KEY):
        self.client = None
        self.key = key
        if url:
            try:
                from redis import Redis
                from redis.backoff import NoBackoff
                from redis.exceptions import RedisError
                from redis.retry import Retry
            except ImportError as exc:
                raise ValueError(
                    "Redis signaling requires uv sync --extra redis"
                ) from exc
            self.client = Redis.from_url(
                url,
                socket_connect_timeout=0.5,
                socket_timeout=3,
                retry=Retry(NoBackoff(), 0),
            )
            self.redis_error = RedisError

    def notify(self) -> None:
        if self.client is None:
            return
        try:
            with self.client.pipeline() as pipeline:
                pipeline.rpush(self.key, "ready")
                pipeline.ltrim(self.key, -64, -1)
                pipeline.expire(self.key, 10)
                pipeline.execute()
        except self.redis_error:
            # The job is already committed. The periodic poll will find it.
            return

    def wait(self) -> None:
        if self.client is not None:
            try:
                self.client.blpop(self.key, timeout=2)
                return
            except self.redis_error:
                pass
        sleep(1)


def configured_wakeup() -> WorkerWakeup:
    return WorkerWakeup(
        os.environ.get("OPSPILOT_REDIS_URL"),
        os.environ.get("OPSPILOT_REDIS_KEY", DEFAULT_KEY),
    )
