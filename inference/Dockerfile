FROM python:3.13-slim

ARG TORCH_BACKEND

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./ 

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN uv sync --frozen --no-dev --extra=${TORCH_BACKEND} --group=inference

COPY inference/ inference/
COPY common/ common/
WORKDIR /app

CMD ["uv", "run", "--no-sync", "python", "-m", "inference.main"]
