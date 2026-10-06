type Destination = {
  name: string;
  address: string;
  region: string;
  latency: number;
  availability: string;
  status: "Healthy" | "Degraded";
};

import { ThemeToggle } from "./theme-toggle";

const destinations: Destination[] = [
  { name: "Google DNS", address: "8.8.8.8", region: "Global", latency: 18, availability: "99.99%", status: "Healthy" },
  { name: "Cloudflare DNS", address: "1.1.1.1", region: "Global", latency: 14, availability: "100%", status: "Healthy" },
  { name: "Quad9 DNS", address: "9.9.9.9", region: "Global", latency: 31, availability: "99.72%", status: "Degraded" },
  { name: "Core gateway", address: "10.0.0.1", region: "Chicago", latency: 3, availability: "100%", status: "Healthy" },
];

const events = [
  { time: "14:32:18", destination: "Cloudflare DNS", address: "1.1.1.1", latency: "13.8 ms", result: "Reply" },
  { time: "14:32:17", destination: "Google DNS", address: "8.8.8.8", latency: "18.4 ms", result: "Reply" },
  { time: "14:32:16", destination: "Quad9 DNS", address: "9.9.9.9", latency: "—", result: "Timeout" },
  { time: "14:32:15", destination: "Core gateway", address: "10.0.0.1", latency: "2.7 ms", result: "Reply" },
  { time: "14:32:14", destination: "Cloudflare DNS", address: "1.1.1.1", latency: "14.1 ms", result: "Reply" },
];

const series = [21, 18, 19, 17, 25, 22, 16, 18, 15, 17, 24, 19, 18, 16, 14, 28, 23, 19, 17, 18, 16, 21, 20, 15];

function SignalIcon() {
  return <span className="signal-icon" aria-hidden="true"><i /><i /><i /></span>;
}

export default function Home() {
  const points = series
    .map((value, index) => `${(index / (series.length - 1)) * 100},${100 - ((value - 10) / 24) * 100}`)
    .join(" ");

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><SignalIcon /></div>
          <div><strong>PingArchive</strong><span>Network observability</span></div>
        </div>
        <nav aria-label="Primary navigation">
          <a className="nav-item active" href="#overview"><span className="nav-glyph">◫</span>Overview</a>
          <a className="nav-item" href="#destinations"><span className="nav-glyph">◎</span>Destinations</a>
          <a className="nav-item" href="#events"><span className="nav-glyph">≋</span>Ping events</a>
          <a className="nav-item" href="/settings"><span className="nav-glyph">⚙</span>Settings</a>
        </nav>
        <div className="sidebar-footer">
          <div className="engine-state"><span className="status-dot" /><div><strong>Engine online</strong><span>Last sample 2s ago</span></div></div>
          <div className="version">PING ENGINE · V0.1</div>
        </div>
      </aside>

      <section className="workspace" id="overview">
        <header className="topbar">
          <div>
            <p className="eyebrow">NETWORK OVERVIEW</p>
            <h1>Good afternoon</h1>
            <p className="subhead">All systems are responding normally.</p>
          </div>
          <div className="topbar-actions">
            <ThemeToggle />
            <button className="icon-button" aria-label="Notifications">●<span className="notification-dot" /></button>
            <a className="primary-button" href="/settings"><span>＋</span> Add destination</a>
          </div>
        </header>

        <section className="metrics" aria-label="Network summary">
          <article className="metric-card"><div className="metric-label"><span>ACTIVE DESTINATIONS</span><span className="metric-icon">◎</span></div><strong>4</strong><p><span className="positive">↑ 1</span> this week</p></article>
          <article className="metric-card"><div className="metric-label"><span>AVERAGE LATENCY</span><span className="metric-icon">⌁</span></div><strong>16.5 <small>ms</small></strong><p><span className="positive">↓ 2.4 ms</span> from yesterday</p></article>
          <article className="metric-card"><div className="metric-label"><span>PACKET LOSS</span><span className="metric-icon">◇</span></div><strong>0.18<small>%</small></strong><p><span className="warning">↑ 0.06%</span> from yesterday</p></article>
          <article className="metric-card"><div className="metric-label"><span>24H AVAILABILITY</span><span className="metric-icon">✓</span></div><strong>99.94<small>%</small></strong><p><span className="positive">Within target</span></p></article>
        </section>

        <section className="dashboard-grid">
          <article className="panel chart-panel">
            <div className="panel-heading">
              <div><h2>Latency history</h2><p>Average response time across all destinations</p></div>
              <div className="range-control" aria-label="Time range"><button>1H</button><button className="selected">24H</button><button>7D</button><button>30D</button></div>
            </div>
            <div className="chart-summary"><strong>16.5 ms</strong><span><i /> Global average</span></div>
            <div className="chart" role="img" aria-label="Latency fluctuated between 14 and 28 milliseconds over the last 24 hours">
              <div className="y-labels"><span>40</span><span>30</span><span>20</span><span>10</span><span>0</span></div>
              <div className="plot">
                <div className="grid-lines"><i /><i /><i /><i /><i /></div>
                <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
                  <defs><linearGradient id="chartFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#55d6be" stopOpacity=".3"/><stop offset="100%" stopColor="#55d6be" stopOpacity="0"/></linearGradient></defs>
                  <polygon points={`0,100 ${points} 100,100`} fill="url(#chartFill)" />
                  <polyline points={points} fill="none" stroke="#55d6be" strokeWidth="1.6" vectorEffect="non-scaling-stroke" />
                </svg>
                <div className="x-labels"><span>12 AM</span><span>6 AM</span><span>12 PM</span><span>6 PM</span><span>Now</span></div>
              </div>
            </div>
          </article>

          <article className="panel health-panel" id="destinations">
            <div className="panel-heading"><div><h2>Destination health</h2><p>Current status</p></div><a href="#events">View all</a></div>
            <div className="destination-list">
              {destinations.map((destination) => (
                <div className="destination" key={destination.address}>
                  <div className={`destination-mark ${destination.status === "Healthy" ? "healthy" : "degraded"}`}><SignalIcon /></div>
                  <div className="destination-name"><strong>{destination.name}</strong><span>{destination.address} · {destination.region}</span></div>
                  <div className="destination-stat"><strong>{destination.latency} ms</strong><span>{destination.availability}</span></div>
                  <span className={`status-badge ${destination.status.toLowerCase()}`}>{destination.status}</span>
                </div>
              ))}
            </div>
          </article>
        </section>

        <section className="panel events-panel" id="events">
          <div className="panel-heading"><div><h2>Recent ping events</h2><p>Latest responses received by the ping engine</p></div><button className="secondary-button">Export data</button></div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>TIME</th><th>DESTINATION</th><th>ADDRESS</th><th>LATENCY</th><th>RESULT</th></tr></thead>
              <tbody>{events.map((event) => (
                <tr key={`${event.time}-${event.address}`}><td className="mono">{event.time}</td><td><strong>{event.destination}</strong></td><td className="mono muted">{event.address}</td><td className="mono">{event.latency}</td><td><span className={`event-result ${event.result.toLowerCase()}`}><i />{event.result}</span></td></tr>
              ))}</tbody>
            </table>
          </div>
        </section>
      </section>
    </main>
  );
}
