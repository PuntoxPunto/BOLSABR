FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BOLSABR_SNAPSHOT_DIR=/data/serving \
    BOLSABR_UNIVERSE_MODE="manual" \
    BOLSABR_UNDERLYINGS="PETR4" \
    BOLSABR_UNIVERSE_LIMIT="20" \
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

CMD ["sh", "-lc", "if [ \"$BOLSABR_UNIVERSE_MODE\" = \"auto\" ]; then python scripts/build_eod_options.py --auto-universe --universe-limit \"$BOLSABR_UNIVERSE_LIMIT\" --min-financial-volume \"$BOLSABR_UNIVERSE_MIN_FINANCIAL_VOLUME\" --output-dir artifacts/chains --publish-dir \"$BOLSABR_SNAPSHOT_DIR\"; else python scripts/build_eod_options.py $BOLSABR_UNDERLYINGS --output-dir artifacts/chains --publish-dir \"$BOLSABR_SNAPSHOT_DIR\"; fi"]
