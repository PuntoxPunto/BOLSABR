FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BOLSABR_SNAPSHOT_DIR=/data/serving

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

CMD ["sh", "-lc", "python scripts/b3_smoke.py && python scripts/publish_snapshot.py artifacts/petr4-option-chain-v0.json --snapshot-dir \"$BOLSABR_SNAPSHOT_DIR\""]
