"use client";

import { useCallback, useEffect, useRef, useState } from "react";
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

type LatencyPoint = { timestamp: string; average_latency_ms: number | null };

export type LatencyChartSeries = {
  destination_id: number;
  name: string;
  color: string;
  points: LatencyPoint[];
};

type LatencyChartProps = {
  series: LatencyChartSeries[];
  rangeLabel: string;
  rangeHours: number;
  refreshSeconds: number;
  onRefreshSecondsChange: (seconds: number) => void;
  onReset: () => void;
};

type StoredSeries = Omit<LatencyChartSeries, "points"> & { points: Map<number, number | null> };
const LIVE_RIGHT_BUFFER_PX = 64;
const GAP_THRESHOLDS: Record<number, number> = {
  1: 12,
  24: 90 * 60,
  168: 9 * 60 * 60,
  720: 36 * 60 * 60,
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

export function LatencyChart({ series, rangeLabel, rangeHours, refreshSeconds, onRefreshSecondsChange, onReset }: LatencyChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const lineRefs = useRef(new Map<number, ISeriesApi<"Line">[]>());
  const dataRef = useRef(new Map<number, StoredSeries>());
  const initializedRef = useRef(false);
  const autoFollowRef = useRef(true);
  const [autoFollow, setAutoFollow] = useState(true);

  const pauseAutoFollow = useCallback(() => {
    autoFollowRef.current = false;
    setAutoFollow(false);
  }, []);

  function resumeAutoFollow() {
    autoFollowRef.current = true;
    setAutoFollow(true);
    chartRef.current?.timeScale().applyOptions({ rightOffsetPixels: LIVE_RIGHT_BUFFER_PX });
    chartRef.current?.timeScale().scrollToRealTime();
  }

  const mergeAndRender = useCallback((incoming: LatencyChartSeries[]) => {
    const chart = chartRef.current;
    if (!chart) return;

    for (const item of incoming) {
      let stored = dataRef.current.get(item.destination_id);
      if (!stored) {
        stored = { destination_id: item.destination_id, name: item.name, color: item.color, points: new Map() };
        dataRef.current.set(item.destination_id, stored);
      }
      stored.name = item.name;
      stored.color = item.color;
      for (const point of item.points) {
        const timestamp = Math.floor(new Date(point.timestamp).getTime() / 1000);
        stored.points.set(timestamp, point.average_latency_ms);
      }

      for (const line of lineRefs.current.get(item.destination_id) ?? []) {
        chart.removeSeries(line);
      }
      lineRefs.current.delete(item.destination_id);

      const sortedPoints = [...stored.points.entries()].sort(([left], [right]) => left - right);
      const segments: LineData<UTCTimestamp>[][] = [];
      let segment: LineData<UTCTimestamp>[] = [];
      let previousTimestamp: number | null = null;
      for (const [time, value] of sortedPoints) {
        const timestampGap = previousTimestamp !== null && time - previousTimestamp > GAP_THRESHOLDS[rangeHours];
        if (value === null) {
          if (segment.length > 0) segments.push(segment);
          segment = [];
          previousTimestamp = time;
          continue;
        }
        if (timestampGap) {
          if (segment.length > 0) segments.push(segment);
          segment = [];
        }
        segment.push({ time: time as UTCTimestamp, value });
        previousTimestamp = time;
      }
      if (segment.length > 0) segments.push(segment);

      const lines = segments.map((points, index) => {
        const line = chart.addSeries(LineSeries, {
          color: stored.color,
          lineWidth: 2,
          title: "",
          priceLineVisible: false,
          lastValueVisible: index === segments.length - 1,
          crosshairMarkerVisible: true,
          crosshairMarkerRadius: 4,
        });
        line.setData(points);
        return line;
      });
      lineRefs.current.set(item.destination_id, lines);
    }
  }, [rangeHours]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const lines = lineRefs.current;
    const storedData = dataRef.current;

    const chart = createChart(container, {
      width: container.clientWidth,
      height: container.clientHeight,
      autoSize: false,
      crosshair: { mode: CrosshairMode.Normal },
      handleScroll: { mouseWheel: true, pressedMouseMove: true, horzTouchDrag: true, vertTouchDrag: false },
      handleScale: { axisPressedMouseMove: true, mouseWheel: true, pinch: true },
      localization: { priceFormatter: (value: number) => `${value.toFixed(2)} ms` },
      rightPriceScale: { autoScale: true, scaleMargins: { top: 0.1, bottom: 0.1 } },
      timeScale: { timeVisible: true, secondsVisible: true, rightOffsetPixels: LIVE_RIGHT_BUFFER_PX, fixLeftEdge: false, fixRightEdge: false },
    });
    applyTheme(chart);
    chartRef.current = chart;

    const resizeObserver = new ResizeObserver(() => {
      chart.resize(container.clientWidth, container.clientHeight);
    });
    resizeObserver.observe(container);

    const themeObserver = new MutationObserver(() => applyTheme(chart));
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });

    const handlePointerMove = (event: PointerEvent) => {
      if (event.buttons !== 0) pauseAutoFollow();
    };
    container.addEventListener("pointermove", handlePointerMove);
    container.addEventListener("wheel", pauseAutoFollow, { passive: true });
    container.addEventListener("touchmove", pauseAutoFollow, { passive: true });

    return () => {
      container.removeEventListener("pointermove", handlePointerMove);
      container.removeEventListener("wheel", pauseAutoFollow);
      container.removeEventListener("touchmove", pauseAutoFollow);
      themeObserver.disconnect();
      resizeObserver.disconnect();
      lines.clear();
      storedData.clear();
      chartRef.current = null;
      chart.remove();
    };
  }, [pauseAutoFollow]);

  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;

    const visibleRange = chart.timeScale().getVisibleRange();
    mergeAndRender(series);

    if (!initializedRef.current) {
      const latestTimestamp = Math.max(
        ...series.flatMap((item) => item.points.map((point) => Math.floor(new Date(point.timestamp).getTime() / 1000))),
      );
      chart.timeScale().setVisibleRange({
        from: (latestTimestamp - (rangeHours * 60 * 60)) as UTCTimestamp,
        to: latestTimestamp as UTCTimestamp,
      });
      chart.timeScale().applyOptions({ rightOffsetPixels: LIVE_RIGHT_BUFFER_PX });
      chart.timeScale().scrollToRealTime();
      initializedRef.current = true;
    } else if (autoFollowRef.current) {
      chart.timeScale().applyOptions({ rightOffsetPixels: LIVE_RIGHT_BUFFER_PX });
      chart.timeScale().scrollToRealTime();
    } else if (visibleRange) {
      chart.timeScale().setVisibleRange(visibleRange);
    }
  }, [mergeAndRender, rangeHours, series]);

  return (
    <div className="latency-chart-shell">
      <div className="chart-meta-row">
        <div className="chart-legend" aria-label="Destination legend">
          {series.map((item) => <span key={item.destination_id}><i style={{ backgroundColor: item.color }} />{item.name}</span>)}
        </div>
        <div className="chart-live-controls">
          <label className="chart-refresh-control">
            <span>Refresh</span>
            <select value={refreshSeconds} onChange={(event) => onRefreshSecondsChange(Number(event.target.value))} aria-label="Chart refresh interval">
              {[1, 5, 20, 60].map((seconds) => <option key={seconds} value={seconds}>{seconds}s</option>)}
            </select>
          </label>
          <div className={`chart-follow-status ${autoFollow ? "active" : "paused"}`} role="status">
            <span><i />{autoFollow ? "Following live data" : "Live follow paused"}</span>
            {!autoFollow && <button type="button" onClick={resumeAutoFollow}>Resume live</button>}
          </div>
          <button className="chart-reset-button" type="button" onClick={onReset}>Reset chart</button>
        </div>
      </div>
      <div
        ref={containerRef}
        className="latency-chart"
        role="img"
        aria-label={`Interactive latency history for ${series.length} destinations, initially showing the last ${rangeLabel}. Drag to pan and use the mouse wheel to zoom.`}
      />
    </div>
  );
}
