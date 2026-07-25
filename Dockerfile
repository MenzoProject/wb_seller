# syntax=docker/dockerfile:1

FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Системные зависимости, необходимые для сборки asyncpg и прочих C-расширений.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./

# Устанавливаем зависимости проекта отдельным слоем для использования кэша Docker.
RUN pip install --no-cache-dir .

COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/logs \
    && chown -R appuser:appuser /app

USER appuser

CMD ["python", "-m", "src.main"]
