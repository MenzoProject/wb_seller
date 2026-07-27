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

COPY pyproject.toml ./
COPY src ./SRC
COPY README.md ./README.md

# Устанавливаем проект и все его зависимости. Каталог src должен уже
# присутствовать на этом шаге: build-backend hatchling собирает пакет
# из pyproject.toml и требует наличия исходников, поэтому объединить
# эту команду с отдельным кэшируемым слоем "только зависимости" без
# генерации requirements.txt невозможно.
RUN pip install --no-cache-dir .

COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY docker-entrypoint.sh ./docker-entrypoint.sh

RUN chmod +x ./docker-entrypoint.sh \
    && useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/logs \
    && chown -R appuser:appuser /app

USER appuser

ENTRYPOINT ["./docker-entrypoint.sh"]
