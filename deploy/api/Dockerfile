FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BOLSABR_SNAPSHOT_DIR=/data/serving \
    PORT=8000

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src

RUN pip install --no-cache-dir .

RUN addgroup --system --gid 1001 bolsabr \
    && adduser --system --uid 1001 --ingroup bolsabr bolsabr \
    && mkdir -p /data/serving \
    && chown -R bolsabr:bolsabr /data/serving

USER bolsabr

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3).read()" || exit 1

CMD ["uvicorn", "bolsabr.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
