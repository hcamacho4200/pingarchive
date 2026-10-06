"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { ThemeToggle } from "../theme-toggle";

type AddressType = "HOST" | "IPV4" | "IPV6";
type LocationZone = "LAN" | "VPN" | "GATEWAY" | "PROVIDER_DNS" | "INTERNET";

type PingDestination = {
  id: number;
  name: string;
  ipv4: string | null;
  ipv6: string | null;
  host: string | null;
  address_type: AddressType;
  location_zone: LocationZone;
  ping_interval: number;
  enabled: boolean;
  created_at: string | null;
  updated_at: string | null;
};

type DestinationForm = {
  name: string;
  address: string;
  addressType: AddressType;
  locationZone: LocationZone;
  pingInterval: number;
  enabled: boolean;
};

type ApiResponse<T> = { data: T };

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8002/api/v1";
const EMPTY_FORM: DestinationForm = {
  name: "",
  address: "",
  addressType: "HOST",
  locationZone: "INTERNET",
  pingInterval: 1,
  enabled: true,
};

function addressFor(destination: PingDestination) {
  return destination.host ?? destination.ipv4 ?? destination.ipv6 ?? "—";
}

function requestBody(form: DestinationForm) {
  return {
    name: form.name.trim(),
    host: form.addressType === "HOST" ? form.address.trim() : null,
    ipv4: form.addressType === "IPV4" ? form.address.trim() : null,
    ipv6: form.addressType === "IPV6" ? form.address.trim() : null,
    address_type: form.addressType,
    location_zone: form.locationZone,
    ping_interval: form.pingInterval,
    enabled: form.enabled,
  };
}

async function apiRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  const payload = await response.json() as ApiResponse<T> | { detail?: string };
  if (!response.ok) {
    throw new Error("detail" in payload && payload.detail ? payload.detail : `Request failed (${response.status})`);
  }
  return (payload as ApiResponse<T>).data;
}

export default function SettingsPage() {
  const [destinations, setDestinations] = useState<PingDestination[]>([]);
  const [form, setForm] = useState<DestinationForm>(EMPTY_FORM);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadDestinations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setDestinations(await apiRequest<PingDestination[]>("/ping_destinations"));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to load destinations");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void loadDestinations(); }, [loadDestinations]);

  function startEditing(destination: PingDestination) {
    setEditingId(destination.id);
    setForm({
      name: destination.name,
      address: addressFor(destination),
      addressType: destination.address_type,
      locationZone: destination.location_zone,
      pingInterval: destination.ping_interval,
      enabled: destination.enabled,
    });
    setError(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function resetForm() {
    setEditingId(null);
    setForm(EMPTY_FORM);
  }

  async function saveDestination(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const destination = await apiRequest<PingDestination>(
        editingId === null ? "/ping_destinations" : `/ping_destinations/${editingId}`,
        { method: editingId === null ? "POST" : "PUT", body: JSON.stringify(requestBody(form)) },
      );
      setDestinations((current) => editingId === null
        ? [...current, destination]
        : current.map((item) => item.id === destination.id ? destination : item));
      resetForm();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to save destination");
    } finally {
      setSaving(false);
    }
  }

  async function toggleDestination(destination: PingDestination) {
    setError(null);
    try {
      const updated = await apiRequest<PingDestination>(`/ping_destinations/${destination.id}`, {
        method: "PUT",
        body: JSON.stringify({
          name: destination.name,
          ipv4: destination.ipv4,
          ipv6: destination.ipv6,
          host: destination.host,
          address_type: destination.address_type,
          location_zone: destination.location_zone,
          ping_interval: destination.ping_interval,
          enabled: !destination.enabled,
        }),
      });
      setDestinations((current) => current.map((item) => item.id === updated.id ? updated : item));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to update destination");
    }
  }

  async function deleteDestination(destination: PingDestination) {
    if (!window.confirm(`Delete ${destination.name}? This cannot be undone.`)) return;
    setError(null);
    try {
      await apiRequest<PingDestination>(`/ping_destinations/${destination.id}`, { method: "DELETE" });
      setDestinations((current) => current.filter((item) => item.id !== destination.id));
      if (editingId === destination.id) resetForm();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to delete destination");
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark"><span className="signal-icon" aria-hidden="true"><i /><i /><i /></span></div><div><strong>PingArchive</strong><span>Network observability</span></div></div>
        <nav aria-label="Primary navigation">
          <a className="nav-item" href="/"><span className="nav-glyph">◫</span>Overview</a>
          <a className="nav-item" href="/#destinations"><span className="nav-glyph">◎</span>Destinations</a>
          <a className="nav-item" href="/#events"><span className="nav-glyph">≋</span>Ping events</a>
          <a className="nav-item active" href="/settings"><span className="nav-glyph">⚙</span>Settings</a>
        </nav>
        <div className="sidebar-footer"><div className="engine-state"><span className="status-dot" /><div><strong>Engine online</strong><span>Configuration service</span></div></div><div className="version">PING ENGINE · V0.1</div></div>
      </aside>

      <section className="workspace settings-workspace">
        <header className="topbar">
          <div><p className="eyebrow">SETTINGS</p><h1>Ping destinations</h1><p className="subhead">Manage the hosts and addresses monitored by the ping engine.</p></div>
          <div className="topbar-actions"><ThemeToggle /></div>
        </header>

        {error && <div className="error-banner" role="alert"><strong>Unable to complete request</strong><span>{error}</span><button onClick={() => setError(null)} aria-label="Dismiss error">×</button></div>}

        <section className="settings-grid">
          <article className="panel destination-form-panel">
            <div className="panel-heading"><div><h2>{editingId === null ? "Add destination" : "Edit destination"}</h2><p>{editingId === null ? "Configure a new ping target" : "Update the selected ping target"}</p></div>{editingId !== null && <button className="text-button" onClick={resetForm}>Cancel</button>}</div>
            <form className="destination-form" onSubmit={saveDestination}>
              <label><span>Name</span><input required maxLength={100} value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="Office gateway" /></label>
              <div className="form-row">
                <label><span>Address type</span><select value={form.addressType} onChange={(event) => setForm({ ...form, addressType: event.target.value as AddressType, address: "" })}><option value="HOST">Hostname</option><option value="IPV4">IPv4</option><option value="IPV6">IPv6</option></select></label>
                <label className="address-field"><span>{form.addressType === "HOST" ? "Hostname" : form.addressType}</span><input required value={form.address} onChange={(event) => setForm({ ...form, address: event.target.value })} placeholder={form.addressType === "HOST" ? "gateway.example.com" : form.addressType === "IPV4" ? "192.168.1.1" : "2001:db8::1"} /></label>
              </div>
              <div className="form-row">
                <label><span>Location zone</span><select value={form.locationZone} onChange={(event) => setForm({ ...form, locationZone: event.target.value as LocationZone })}><option value="LAN">LAN</option><option value="VPN">VPN</option><option value="GATEWAY">Gateway</option><option value="PROVIDER_DNS">Provider DNS</option><option value="INTERNET">Internet</option></select></label>
                <label><span>Ping interval</span><select value={form.pingInterval} onChange={(event) => setForm({ ...form, pingInterval: Number(event.target.value) })}><option value={1}>Every second</option><option value={2}>Every 2 seconds</option><option value={5}>Every 5 seconds</option><option value={10}>Every 10 seconds</option><option value={60}>Every minute</option><option value={300}>Every 5 minutes</option></select></label>
              </div>
              <label className="checkbox-label"><input type="checkbox" checked={form.enabled} onChange={(event) => setForm({ ...form, enabled: event.target.checked })} /><span><strong>Enable destination</strong><small>Begin monitoring as soon as it is saved</small></span></label>
              <button className="primary-button form-submit" type="submit" disabled={saving}>{saving ? "Saving…" : editingId === null ? "Add destination" : "Save changes"}</button>
            </form>
          </article>

          <article className="panel destination-manager">
            <div className="panel-heading"><div><h2>Configured destinations</h2><p>{destinations.length} {destinations.length === 1 ? "destination" : "destinations"}</p></div><button className="secondary-button" onClick={() => void loadDestinations()} disabled={loading}>Refresh</button></div>
            {loading ? <div className="empty-state">Loading destinations…</div> : destinations.length === 0 ? <div className="empty-state"><strong>No destinations configured</strong><span>Add your first ping target using the form.</span></div> : (
              <div className="managed-list">{destinations.map((destination) => (
                <div className={`managed-destination ${destination.enabled ? "" : "disabled"}`} key={destination.id}>
                  <div className={`destination-mark ${destination.enabled ? "healthy" : "degraded"}`}><span className="signal-icon" aria-hidden="true"><i /><i /><i /></span></div>
                  <div className="managed-details"><div><strong>{destination.name}</strong><span className={`status-badge ${destination.enabled ? "healthy" : "degraded"}`}>{destination.enabled ? "Enabled" : "Disabled"}</span></div><span>{addressFor(destination)} · {destination.location_zone.replace("_", " ")} · {destination.ping_interval}s</span></div>
                  <div className="row-actions"><button className="text-button" onClick={() => startEditing(destination)}>Edit</button><button className="text-button" onClick={() => void toggleDestination(destination)}>{destination.enabled ? "Disable" : "Enable"}</button><button className="text-button danger-button" onClick={() => void deleteDestination(destination)}>Delete</button></div>
                </div>
              ))}</div>
            )}
          </article>
        </section>
      </section>
    </main>
  );
}
