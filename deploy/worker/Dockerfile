FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BOLSABR_SNAPSHOT_DIR=/data/serving \
    BOLSABR_UNIVERSE_MODE="auto" \
    BOLSABR_UNDERLYINGS="PETR4" \
    BOLSABR_UNIVERSE_LIMIT="50" \
    BOLSABR_UNIVERSE_KIND="stocks" \
    BOLSABR_UNIVERSE_MIN_FINANCIAL_VOLUME="0"

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
COPY scripts ./scripts

RUN pip install --no-cache-dir .

RUN addgroup --system --gid 1001 bolsabr \
    && adduser --system --uid 1001 --ingroup bolsabr bolsabr \
    && mkdir -p /data/serving /app/artifacts \
    && chown -R bolsabr:bolsabr /data/serving /app/artifacts

USER bolsabr

CMD ["python", "scripts/run_eod_publisher.py"]
