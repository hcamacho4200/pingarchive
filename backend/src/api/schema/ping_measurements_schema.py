"""API schemas for QuestDB ping-measurement summaries."""

from datetime import datetime

from pydantic import BaseModel


class LatencyPointSchema(BaseModel):
    """One aggregated latency bucket."""

    timestamp: datetime
    average_latency_ms: float | None


class LatencySeriesSchema(BaseModel):
    """Latency history for one destination."""

    destination_id: int
    name: str
    points: list[LatencyPointSchema]


class LatencyHistorySchema(BaseModel):
    """A bounded window of latency history grouped by destination."""

    start_time: datetime
    end_time: datetime
    latency_series: list[LatencySeriesSchema]


class DestinationHealthSchema(BaseModel):
    """Health summary for one configured ping destination."""

    destination_id: int
    name: str
    address: str
    average_latency_ms: float | None
    availability_pct: float
    packet_loss_pct: float
    last_seen: datetime
    latest_outcome: str
    status: str


class PingEventSchema(BaseModel):
    """One recent ping measurement."""

    timestamp: datetime
    destination_name: str
    address: str
    latency_ms: float | None
    outcome: str


class PingOverviewSchema(BaseModel):
    """QuestDB-backed data needed by the overview page."""

    range_hours: int
    average_latency_ms: float | None
    availability_pct: float | None
    packet_loss_pct: float | None
    latency_series: list[LatencySeriesSchema]
    destinations: list[DestinationHealthSchema]
    recent_events: list[PingEventSchema]
