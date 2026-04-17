FROM python:3.10-slim

ARG TORCH_BACKEND

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./ 

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN uv sync --frozen --no-dev --extra=${TORCH_BACKEND}

COPY inference/ inference/
WORKDIR /app

CMD ["uv", "run", "python", "-m", "inference.main"]
