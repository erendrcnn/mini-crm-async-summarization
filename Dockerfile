# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends build-essential supervisor && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY app ./app
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic
COPY supervisord.conf ./supervisord.conf

# Install
RUN pip install --no-cache-dir -U pip setuptools wheel \
    && pip install --no-cache-dir -e .

# Runtime
ENV PORT=8000
EXPOSE 8000

# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["supervisord", "-c", "/app/supervisord.conf"]