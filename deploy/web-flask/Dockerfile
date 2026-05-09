FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app --shell /usr/sbin/nologin app

COPY core/python-renderer/requirements.txt ./core/python-renderer/requirements.txt
COPY apps/web-flask/requirements.txt ./apps/web-flask/requirements.txt

RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir -r apps/web-flask/requirements.txt

COPY apps/web-flask ./apps/web-flask
COPY core/python-renderer ./core/python-renderer
COPY assets/previews ./assets/previews
COPY LICENSE.md ./LICENSE.md

RUN chown -R app:app /app

USER app

EXPOSE 8000

CMD ["sh", "-c", "gunicorn --chdir /app/apps/web-flask --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-2} --timeout ${GUNICORN_TIMEOUT:-120} --access-logfile - --error-logfile - app:app"]
