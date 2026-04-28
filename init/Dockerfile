FROM python:3.13-slim

ARG TORCH_BACKEND

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

RUN uv sync --frozen --no-dev --group=init

COPY init/ init/
COPY common/ common/

WORKDIR /app

CMD ["uv", "run", "--no-sync", "python", "-m", "init.main"]
