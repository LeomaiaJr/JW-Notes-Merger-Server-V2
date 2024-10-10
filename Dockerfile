FROM python:3.12-slim

RUN pip install poetry

WORKDIR /app

COPY pyproject.toml poetry.lock ./
COPY app ./app

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

RUN pip install gunicorn

EXPOSE 8000

CMD ["gunicorn", "app.server:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--log-level", "info", "--access-logfile", "-", "--error-logfile", "-"]