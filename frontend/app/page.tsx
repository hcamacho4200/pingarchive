"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { LatencyChart } from "./latency-chart";
import { ThemeToggle } from "./theme-toggle";

type TimeRange = 1 | 24 | 168 | 720;
type LatencyPoint = { timestamp: string; average_latency_ms: number | null };
type LatencySeries = { destination_id: number; name: string; points: LatencyPoint[] };
type DestinationHealth = {
  destination_id: number;
  name: string;
  address: string;
  average_latency_ms: number | null;
  availability_pct: number;
  last_seen: string;
  latest_outcome: string;
  status: "Healthy" | "Degraded";
};
type PingEvent = {
  timestamp: string;
  destination_name: string;
  address: string;
  latency_ms: number | null;
  outcome: string;
};
type OverviewData = {
  range_hours: number;
  average_latency_ms: number | null;
  availability_pct: number | null;
  packet_loss_pct: number | null;
  latency_series: LatencySeries[];
  destinations: DestinationHealth[];
  recent_events: PingEvent[];
};
type ApiResponse<T> = { data: T };

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8002/api/v1";
const RANGE_LABELS: Record<TimeRange, string> = { 1: "1H", 24: "24H", 168: "7D", 720: "30D" };
const SERIES_COLORS = ["#0d9488", "#4f7cff", "#e08b37", "#b45ac4", "#d64f6b", "#22a6c7", "#84a344", "#8b6fd9"];

function SignalIcon() {
  return <span className="signal-icon" aria-hidden="true"><i /><i /><i /></span>;
}

function formatNumber(value: number | null, digits = 1) {
  return value === null ? "—" : value.toFixed(digits);
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" }).format(new Date(value));
}

function formatLastSeen(value: string) {
  const seconds = Math.max(0, Math.round((Date.now() - new Date(value).getTime()) / 1000));
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  return `${Math.floor(seconds / 3600)}h ago`;
}

export default function Home() {
  const [range, setRange] = useState<TimeRange>(24);
  const [chartResetKey, setChartResetKey] = useState(0);
  const [refreshSeconds, setRefreshSeconds] = useState(5);
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const requestIdRef = useRef(0);

  const loadOverview = useCallback(async (selectedRange: TimeRange) => {
    const requestId = ++requestIdRef.current;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/ping_measurements/overview?hours=${selectedRange}`, { cache: "no-store" });
      const payload = await response.json() as ApiResponse<OverviewData> | { detail?: string };
      if (!response.ok) throw new Error("detail" in payload && payload.detail ? payload.detail : `Request failed (${response.status})`);
      if (requestId === requestIdRef.current) setOverview((payload as ApiResponse<OverviewData>).data);
    } catch (requestError) {
      if (requestId === requestIdRef.current) {
        setError(requestError instanceof Error ? requestError.message : "Unable to load QuestDB measurements");
      }
    } finally {
      if (requestId === requestIdRef.current) setLoading(false);
    }
  }, []);

  useEffect(() => { void loadOverview(range); }, [chartResetKey, loadOverview, range]);
  useEffect(() => {
    const timer = window.setInterval(() => void loadOverview(range), refreshSeconds * 1000);
    return () => window.clearInterval(timer);
  }, [loadOverview, range, refreshSeconds]);

  const chart = useMemo(() => {
    const sourceSeries = overview?.latency_series ?? [];
    return { series: sourceSeries.map((item, seriesIndex) => ({ ...item, color: SERIES_COLORS[seriesIndex % SERIES_COLORS.length] })) };
  }, [overview]);

  const destinations = overview?.destinations ?? [];
  const events = overview?.recent_events ?? [];
  const allHealthy = destinations.length > 0 && destinations.every((destination) => destination.status === "Healthy");

  function selectRange(hours: TimeRange) {
    setOverview(null);
    setRange(hours);
    setChartResetKey((value) => value + 1);
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark"><SignalIcon /></div><div><strong>PingArchive</strong><span>Network observability</span></div></div>
        <nav aria-label="Primary navigation">
          <a className="nav-item active" href="#overview"><span className="nav-glyph">◫</span>Overview</a>
          <a className="nav-item" href="#destinations"><span className="nav-glyph">◎</span>Destinations</a>
          <a className="nav-item" href="#events"><span className="nav-glyph">≋</span>Ping events</a>
          <a className="nav-item" href="/settings"><span className="nav-glyph">⚙</span>Settings</a>
        </nav>
        <div className="sidebar-footer"><div className="engine-state"><span className={`status-dot ${error ? "status-error" : ""}`} /><div><strong>{error ? "Data unavailable" : "QuestDB connected"}</strong><span>{loading ? "Refreshing…" : `Updates every ${refreshSeconds}s`}</span></div></div><div className="version">PING ENGINE · V0.1</div></div>
      </aside>

      <section className="workspace" id="overview">
        <header className="topbar">
          <div><p className="eyebrow">NETWORK OVERVIEW</p><h1>Network health</h1><p className="subhead">{error ? "Live measurements are temporarily unavailable." : allHealthy ? "All monitored destinations are responding normally." : destinations.length ? "One or more destinations need attention." : "Waiting for the first ping measurements."}</p></div>
          <div className="topbar-actions"><ThemeToggle /><button className="icon-button" aria-label="Refresh measurements" onClick={() => void loadOverview(range)}>↻<span className="notification-dot" /></button><a className="primary-button" href="/settings"><span>＋</span> Add destination</a></div>
        </header>

        {error && <div className="error-banner overview-error" role="alert"><strong>QuestDB data unavailable</strong><span>{error}</span><button onClick={() => void loadOverview(range)}>Retry</button></div>}

        <section className="metrics" aria-label="Network summary">
          <article className="metric-card"><div className="metric-label"><span>OBSERVED DESTINATIONS</span><span className="metric-icon">◎</span></div><strong>{destinations.length}</strong><p>{loading ? "Refreshing…" : `Last ${RANGE_LABELS[range]}`}</p></article>
          <article className="metric-card"><div className="metric-label"><span>AVERAGE LATENCY</span><span className="metric-icon">⌁</span></div><strong>{formatNumber(overview?.average_latency_ms ?? null)} <small>ms</small></strong><p><span className="positive">Live</span> QuestDB aggregate</p></article>
          <article className="metric-card"><div className="metric-label"><span>PACKET LOSS</span><span className="metric-icon">◇</span></div><strong>{formatNumber(overview?.packet_loss_pct ?? null, 2)}<small>%</small></strong><p>Across the selected range</p></article>
          <article className="metric-card"><div className="metric-label"><span>AVAILABILITY</span><span className="metric-icon">✓</span></div><strong>{formatNumber(overview?.availability_pct ?? null, 2)}<small>%</small></strong><p><span className={allHealthy ? "positive" : "warning"}>{allHealthy ? "Within target" : "Review health"}</span></p></article>
        </section>

        <section className="dashboard-grid">
          <article className="panel chart-panel">
            <div className="panel-heading"><div><h2>Latency history</h2><p>Average reply time from QuestDB</p></div><div className="range-control" aria-label="Time range">{(Object.keys(RANGE_LABELS).map(Number) as TimeRange[]).map((hours) => <button key={hours} className={range === hours ? "selected" : ""} onClick={() => selectRange(hours)}>{RANGE_LABELS[hours]}</button>)}</div></div>
            <div className="chart-summary"><strong>{formatNumber(overview?.average_latency_ms ?? null)} ms</strong><span>Average across {chart.series.length} destination{chart.series.length === 1 ? "" : "s"}</span></div>
            {chart.series.length ? <LatencyChart key={`${range}-${chartResetKey}`} series={chart.series} rangeLabel={RANGE_LABELS[range]} rangeHours={range} refreshSeconds={refreshSeconds} onRefreshSecondsChange={setRefreshSeconds} /> : <div className="chart-empty">{loading ? "Loading latency measurements…" : "No latency measurements in this time range."}</div>}
          </article>

          <article className="panel health-panel" id="destinations">
            <div className="panel-heading"><div><h2>Destination health</h2><p>QuestDB measurements · {RANGE_LABELS[range]}</p></div><a href="/settings">Manage</a></div>
            {destinations.length ? <div className="destination-list">{destinations.map((destination) => (
              <div className="destination" key={destination.destination_id}><div className={`destination-mark ${destination.status === "Healthy" ? "healthy" : "degraded"}`}><SignalIcon /></div><div className="destination-name"><strong>{destination.name}</strong><span>{destination.address} · {formatLastSeen(destination.last_seen)}</span></div><div className="destination-stat"><strong>{formatNumber(destination.average_latency_ms)} ms</strong><span>{destination.availability_pct.toFixed(2)}%</span></div><span className={`status-badge ${destination.status.toLowerCase()}`}>{destination.status}</span></div>
            ))}</div> : <div className="empty-state"><strong>{loading ? "Loading health data…" : "No destination data"}</strong><span>Measurements will appear after the ping engine writes to QuestDB.</span></div>}
          </article>
        </section>

        <section className="panel events-panel" id="events">
          <div className="panel-heading"><div><h2>Recent ping events</h2><p>Latest measurements stored in QuestDB</p></div><button className="secondary-button" onClick={() => void loadOverview(range)}>Refresh</button></div>
          {events.length ? <div className="table-wrap"><table><thead><tr><th>TIME</th><th>DESTINATION</th><th>ADDRESS</th><th>LATENCY</th><th>RESULT</th></tr></thead><tbody>{events.map((event) => (
            <tr key={`${event.timestamp}-${event.destination_name}`}><td className="mono">{formatTime(event.timestamp)}</td><td><strong>{event.destination_name}</strong></td><td className="mono muted">{event.address}</td><td className="mono">{event.latency_ms === null ? "—" : `${event.latency_ms.toFixed(2)} ms`}</td><td><span className={`event-result ${event.outcome === "reply" ? "reply" : "timeout"}`}><i />{event.outcome.replace("_", " ")}</span></td></tr>
          ))}</tbody></table></div> : <div className="empty-state compact-empty">No recent ping events.</div>}
        </section>
      </section>
    </main>
  );
}
