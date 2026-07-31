FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN addgroup --system autosales && adduser --system --ingroup autosales autosales

COPY pyproject.toml README.md ./
COPY autosales/__init__.py ./autosales/__init__.py

RUN pip install --upgrade pip && pip install .

COPY autosales ./autosales
COPY scripts ./scripts
COPY alembic.ini ./
COPY alembic ./alembic

USER autosales

EXPOSE 8000
CMD ["uvicorn", "autosales.main:app", "--host", "0.0.0.0", "--port", "8000"]
