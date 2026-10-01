FROM python:3.12.11-slim-bookworm AS builder

WORKDIR /build
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12.11-slim-bookworm AS runtime

ENV HOME=/home/app \
    PATH=/home/app/.local/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system app && useradd --system --gid app --create-home app
WORKDIR /app
COPY --from=builder --chown=app:app /root/.local /home/app/.local
COPY --chown=app:app . .
RUN mkdir -p /app/instance/repositories && chown -R app:app /app/instance

USER app
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=3)" || exit 1

CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:5000 --workers ${GUNICORN_WORKERS:-2} --access-logfile - --error-logfile - wsgi:app"]
