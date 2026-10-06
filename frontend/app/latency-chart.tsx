"use client";

import { useEffect, useRef } from "react";
import {
  ColorType,
  CrosshairMode,
  LineSeries,
  createChart,
  type IChartApi,
  type ISeriesApi,
  type LineData,
  type UTCTimestamp,
} from "lightweight-charts";

type LatencyPoint = { timestamp: string; average_latency_ms: number };

export type LatencyChartSeries = {
  destination_id: number;
  name: string;
  color: string;
  points: LatencyPoint[];
};

type LatencyChartProps = {
  series: LatencyChartSeries[];
  rangeLabel: string;
};

function chartColors() {
  const light = document.documentElement.dataset.theme === "light";
  return {
    text: light ? "#667680" : "#778691",
    grid: light ? "#dce4e8" : "#202c35",
    border: light ? "#d4dde1" : "#26343e",
  };
}

function applyTheme(chart: IChartApi) {
  const colors = chartColors();
  chart.applyOptions({
    layout: { background: { type: ColorType.Solid, color: "transparent" }, textColor: colors.text, fontSize: 11 },
    grid: { vertLines: { color: colors.grid }, horzLines: { color: colors.grid } },
    rightPriceScale: { borderColor: colors.border },
    timeScale: { borderColor: colors.border },
  });
}

function toLineData(points: LatencyPoint[]): LineData<UTCTimestamp>[] {
  const byTimestamp = new Map<number, number>();
  for (const point of points) {
    byTimestamp.set(Math.floor(new Date(point.timestamp).getTime() / 1000), point.average_latency_ms);
  }
  return [...byTimestamp.entries()]
    .sort(([left], [right]) => left - right)
    .map(([time, value]) => ({ time: time as UTCTimestamp, value }));
}

export function LatencyChart({ series, rangeLabel }: LatencyChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const lineRefs = useRef(new Map<number, ISeriesApi<"Line">>());
  const initializedRef = useRef(false);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const lines = lineRefs.current;

    const chart = createChart(container, {
      width: container.clientWidth,
      height: container.clientHeight,
      autoSize: false,
      crosshair: { mode: CrosshairMode.Normal },
      handleScroll: { mouseWheel: true, pressedMouseMove: true, horzTouchDrag: true, vertTouchDrag: false },
      handleScale: { axisPressedMouseMove: true, mouseWheel: true, pinch: true },
      localization: { priceFormatter: (value: number) => `${value.toFixed(2)} ms` },
      rightPriceScale: { autoScale: true, scaleMargins: { top: 0.1, bottom: 0.1 } },
      timeScale: { timeVisible: true, secondsVisible: true, rightOffset: 3, fixLeftEdge: false, fixRightEdge: false },
    });
    applyTheme(chart);
    chartRef.current = chart;

    const resizeObserver = new ResizeObserver(() => {
      chart.resize(container.clientWidth, container.clientHeight);
    });
    resizeObserver.observe(container);

    const themeObserver = new MutationObserver(() => applyTheme(chart));
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });

    return () => {
      themeObserver.disconnect();
      resizeObserver.disconnect();
      lines.clear();
      chartRef.current = null;
      chart.remove();
    };
  }, []);

  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;

    const visibleRange = chart.timeScale().getVisibleLogicalRange();
    const wasFollowingLatest = !initializedRef.current || chart.timeScale().scrollPosition() <= 3;
    const activeIds = new Set(series.map((item) => item.destination_id));

    for (const [destinationId, line] of lineRefs.current) {
      if (!activeIds.has(destinationId)) {
        chart.removeSeries(line);
        lineRefs.current.delete(destinationId);
      }
    }

    for (const item of series) {
      let line = lineRefs.current.get(item.destination_id);
      if (!line) {
        line = chart.addSeries(LineSeries, {
          color: item.color,
          lineWidth: 2,
          title: item.name,
          priceLineVisible: false,
          lastValueVisible: true,
          crosshairMarkerVisible: true,
          crosshairMarkerRadius: 4,
        });
        lineRefs.current.set(item.destination_id, line);
      } else {
        line.applyOptions({ color: item.color, title: item.name });
      }
      line.setData(toLineData(item.points));
    }

    if (!initializedRef.current) {
      chart.timeScale().fitContent();
      initializedRef.current = true;
    } else if (wasFollowingLatest) {
      chart.timeScale().scrollToRealTime();
    } else if (visibleRange) {
      chart.timeScale().setVisibleLogicalRange(visibleRange);
    }
  }, [series]);

  return (
    <div
      ref={containerRef}
      className="latency-chart"
      role="img"
      aria-label={`Interactive latency history for ${series.length} destinations over the last ${rangeLabel}. Drag to pan and use the mouse wheel to zoom.`}
    />
  );
}
