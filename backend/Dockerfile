FROM python:3.10-slim

ARG TORCH_BACKEND

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./ 

RUN uv sync --frozen --no-dev

COPY backend/ backend/
COPY common/ common/
WORKDIR /app

CMD ["uv", "run", "--no-sync", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
