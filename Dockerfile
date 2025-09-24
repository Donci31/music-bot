FROM node:24-alpine AS node_base

FROM ghcr.io/astral-sh/uv:python3.13-alpine

WORKDIR /app/

COPY --from=node_base /usr/local/bin/node /usr/local/bin/

COPY pyproject.toml uv.lock .python-version ./

RUN apk add --no-cache ffmpeg && \
    uv sync --frozen --no-dev --compile-bytecode

COPY ./ ./

ENTRYPOINT ["uv", "run", "--no-sync", "main.py"]
