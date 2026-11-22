FROM ghcr.io/astral-sh/uv:0.13.9 AS uv
FROM python:3.12-slim

COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_PYTHON_DOWNLOADS=never \
    UV_HTTP_TIMEOUT=60 \
    UV_CONCURRENT_DOWNLOADS=8 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    OPSPILOT_DB=/data/opspilot.sqlite3 \
    OPSPILOT_CAPTURES=/app/testbed/scenarios

ARG OPSPILOT_SHARED=0
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    set --; \
    if [ "$OPSPILOT_SHARED" = 1 ]; then set -- --extra postgres --extra redis; fi; \
    uv sync --locked --no-dev --no-install-project "$@"
COPY opspilot ./opspilot
COPY testbed ./testbed
RUN --mount=type=cache,target=/root/.cache/uv \
    set --; \
    if [ "$OPSPILOT_SHARED" = 1 ]; then set -- --extra postgres --extra redis; fi; \
    uv sync --locked --no-dev --no-editable "$@" \
    && chmod -R a+rX /app/testbed \
    && groupadd --gid 10001 opspilot \
    && useradd --uid 10001 --gid 10001 --no-create-home opspilot \
    && install -d -o 10001 -g 10001 /data

USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "opspilot.apps.api.main:local_app", "--factory", "--host", "0.0.0.0"]
