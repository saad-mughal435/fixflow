# FixFlow API — Django + gunicorn.
FROM python:3.14-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# A throwaway key is fine — collectstatic touches no secrets or the DB.
RUN SECRET_KEY=build DEBUG=false python manage.py collectstatic --no-input

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
