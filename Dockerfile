FROM nikolaik/python-nodejs:python3.13-nodejs24-alpine

WORKDIR /app/

COPY pyproject.toml uv.lock .python-version ./

RUN apk add --no-cache ffmpeg && \
    uv sync --frozen --no-dev --compile-bytecode

COPY ./ ./

ENTRYPOINT ["uv", "run", "--no-sync", "main.py"]
