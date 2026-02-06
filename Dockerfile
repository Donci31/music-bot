FROM ghcr.io/astral-sh/uv:python3.14-alpine

WORKDIR /app/

COPY pyproject.toml uv.lock .python-version ./

RUN apk add --no-cache ffmpeg=8.0.1-r1 && \
  uv sync --frozen --no-dev --compile-bytecode

COPY ./ ./

ENTRYPOINT ["uv", "run", "--no-sync", "main.py"]
