FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip poetry

COPY pyproject.toml poetry.lock* README.md* ./
RUN poetry install --only main --no-root

COPY main.py filemanager.py schemas.py ./
COPY files ./files

EXPOSE 8000

CMD ["uvicorn", "main:main_app", "--host", "0.0.0.0", "--port", "8000"]
