"use client";

import { useMemo, useState } from "react";

import type {
  OptionHistoryPayload,
  OptionHistoryPoint,
} from "@/lib/option-chain-types";

type MetricKey = "last" | "iv" | "open_interest" | "volume";

type ChartDefinition = {
  key: MetricKey;
  title: string;
  eyebrow: string;
  format: (value: number) => string;
};

const CHARTS: ChartDefinition[] = [
  {
    key: "last",
    title: "Preço",
    eyebrow: "Último negócio",
    format: (value) =>
      `R$ ${value.toLocaleString("pt-BR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}`,
  },
  {
    key: "iv",
    title: "Volatilidade implícita",
    eyebrow: "IV",
    format: (value) =>
      `${(value * 100).toLocaleString("pt-BR", {
        maximumFractionDigits: 2,
      })}%`,
  },
  {
    key: "open_interest",
    title: "Open Interest",
    eyebrow: "Posições abertas",
    format: compact,
  },
  {
    key: "volume",
    title: "Volume",
    eyebrow: "Quantidade negociada",
    format: compact,
  },
];

function compact(value: number) {
  const abs = Math.abs(value);
  if (abs >= 1_000_000) {
    return `${(value / 1_000_000).toLocaleString("pt-BR", {
      maximumFractionDigits: 2,
    })}M`;
  }
  if (abs >= 1_000) {
    return `${(value / 1_000).toLocaleString("pt-BR", {
      maximumFractionDigits: 1,
    })}k`;
  }
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 0 });
}

function datePt(iso: string) {
  const [year, month, day] = iso.split("-");
  return `${day}/${month}/${year}`;
}

function sourceLabel(source: string) {
  if (source === "BOLSABR_SNAPSHOT") return "Snapshot BOLSABR";
  if (source === "B3_COTAHIST_BACKFILL") return "B3 COTAHIST";
  return source;
}

function metricValue(point: OptionHistoryPoint, key: MetricKey) {
  return point[key];
}

function MetricChart({
  history,
  definition,
}: {
  history: OptionHistoryPayload;
  definition: ChartDefinition;
}) {
  const plotted = useMemo(
    () =>
      history.points
        .map((point, sourceIndex) => ({
          point,
          sourceIndex,
          value: metricValue(point, definition.key),
        }))
        .filter(
          (
            item,
          ): item is {
            point: OptionHistoryPoint;
            sourceIndex: number;
            value: number;
          } => typeof item.value === "number" && Number.isFinite(item.value),
        ),
    [history.points, definition.key],
  );

  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  if (plotted.length < 2) {
    return (
      <article className="history-card">
        <div className="history-card-head">
          <div>
            <div className="eyebrow">{definition.eyebrow}</div>
            <h3>{definition.title}</h3>
          </div>
        </div>
        <div className="history-empty">
          <strong>Histórico em formação</strong>
          <span>
            Este gráfico precisa de pelo menos duas observações EOD reais.
          </span>
        </div>
      </article>
    );
  }

  const width = 560;
  const height = 190;
  const left = 26;
  const right = 18;
  const top = 22;
  const bottom = 30;
  const plotWidth = width - left - right;
  const plotHeight = height - top - bottom;

  const values = plotted.map((item) => item.value);
  let min = Math.min(...values);
  let max = Math.max(...values);
  if (min === max) {
    const pad = Math.max(Math.abs(min) * 0.02, 0.01);
    min -= pad;
    max += pad;
  } else {
    const pad = (max - min) * 0.08;
    min -= pad;
    max += pad;
  }

  const coordinates = plotted.map((item, index) => {
    const x =
      plotted.length === 1
        ? left + plotWidth / 2
        : left + (index / (plotted.length - 1)) * plotWidth;
    const y = top + ((max - item.value) / (max - min)) * plotHeight;
    return { ...item, x, y };
  });

  const active =
    activeIndex == null
      ? coordinates[coordinates.length - 1]
      : coordinates[activeIndex];

  return (
    <article className="history-card">
      <div className="history-card-head">
        <div>
          <div className="eyebrow">{definition.eyebrow}</div>
          <h3>{definition.title}</h3>
        </div>
        <strong>{definition.format(active.value)}</strong>
      </div>

      <div className="history-chart-plot">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          role="img"
          aria-label={`Histórico EOD de ${definition.title}`}
        >
          <line
            className="history-grid-line"
            x1={left}
            x2={width - right}
            y1={top}
            y2={top}
          />
          <line
            className="history-grid-line"
            x1={left}
            x2={width - right}
            y1={top + plotHeight / 2}
            y2={top + plotHeight / 2}
          />
          <line
            className="history-grid-line"
            x1={left}
            x2={width - right}
            y1={height - bottom}
            y2={height - bottom}
          />

          <polyline
            className="history-line"
            points={coordinates
              .map((item) => `${item.x},${item.y}`)
              .join(" ")}
            fill="none"
          />

          {coordinates.map((item, index) => (
            <circle
              key={`${item.point.ref_date}-${definition.key}`}
              className={
                index === (activeIndex ?? coordinates.length - 1)
                  ? "history-point active"
                  : "history-point"
              }
              cx={item.x}
              cy={item.y}
              r={index === (activeIndex ?? coordinates.length - 1) ? 5 : 3.5}
              tabIndex={0}
              role="button"
              aria-label={`${datePt(item.point.ref_date)}: ${definition.format(item.value)}; ${item.point.quote_state}; ${sourceLabel(item.point.source)}`}
              onMouseEnter={() => setActiveIndex(index)}
              onFocus={() => setActiveIndex(index)}
            />
          ))}
        </svg>
      </div>

      <div className="history-chart-axis">
        <span>{datePt(coordinates[0].point.ref_date)}</span>
        <span>{datePt(coordinates[coordinates.length - 1].point.ref_date)}</span>
      </div>

      <div className="history-active">
        <span>{datePt(active.point.ref_date)}</span>
        <strong>{definition.format(active.value)}</strong>
        <span>{active.point.quote_state}</span>
        <span>{sourceLabel(active.point.source)}</span>
        <span>via {active.point.price_basis ?? "—"}</span>
      </div>
    </article>
  );
}

export default function HistoryCharts({
  history,
}: {
  history: OptionHistoryPayload | null;
}) {
  if (!history) {
    return (
      <section className="history-section">
        <div className="history-section-head">
          <div>
            <div className="eyebrow">Histórico EOD</div>
            <h2>Série ainda indisponível</h2>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="history-section" aria-labelledby="history-title">
      <div className="history-section-head">
        <div>
          <div className="eyebrow">Histórico EOD</div>
          <h2 id="history-title">Evolução do contrato</h2>
          <p>
            {history.observations} observações entre {datePt(history.start_date)} e{" "}
            {datePt(history.end_date)}. Cada ponto preserva sua fonte EOD;
            não há preenchimento de dias ausentes.
          </p>
        </div>
      </div>

      <div className="history-grid">
        {CHARTS.map((definition) => (
          <MetricChart
            key={definition.key}
            history={history}
            definition={definition}
          />
        ))}
      </div>
    </section>
  );
}
