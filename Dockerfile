FROM nikolaik/python-nodejs

RUN apt-get -y update && apt-get install -y ffmpeg	

WORKDIR /app/

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync

COPY ./ ./

ENTRYPOINT ["uv", "run", "main.py"]
