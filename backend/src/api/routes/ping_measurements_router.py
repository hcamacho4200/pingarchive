"""QuestDB-backed ping measurement routes."""

import logging

from fastapi import APIRouter, HTTPException, Query

from api.request_context import build_meta, request_meta_context
from api.schema.api_response_schema import ApiResponse
from api.schema.ping_measurements_schema import (
    DestinationHealthSchema,
    LatencyPointSchema,
    LatencySeriesSchema,
    PingEventSchema,
    PingOverviewSchema,
)
from environment import get_settings
from questdb_client import QuestDBClient, QuestDBError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ping_measurements", tags=["ping_measurements"])

SAMPLE_INTERVALS = {1: "5s", 24: "1h", 168: "6h", 720: "1d"}


@router.get("/overview", summary="Get QuestDB data for the overview dashboard", response_model=ApiResponse[PingOverviewSchema])
def ping_overview(hours: int = Query(default=24)):
    """Return latency history and destination health for a supported time range."""
    if hours not in SAMPLE_INTERVALS:
        raise HTTPException(status_code=400, detail="hours must be one of 1, 24, 168, or 720")

    interval = SAMPLE_INTERVALS[hours]
    client = QuestDBClient(get_settings().questdb_address)
    latency_sql = f"""
        SELECT
            sent_time AS timestamp,
            destination_id,
            destination_name,
            avg(rtt_us) / 1000.0 AS average_latency_ms
        FROM ping_measurements
        WHERE sent_time >= dateadd('h', -{hours}, now()) AND outcome = 'reply'
        SAMPLE BY {interval} ALIGN TO CALENDAR
    """
    health_sql = f"""
        SELECT
            destination_id,
            destination_name,
            last(target_address) AS target_address,
            avg(rtt_us) / 1000.0 AS average_latency_ms,
            100.0 * count(rtt_us) / count() AS availability_pct,
            last(sent_time) AS last_seen,
            last(outcome) AS latest_outcome
        FROM ping_measurements
        WHERE sent_time >= dateadd('h', -{hours}, now())
    """
    recent_sql = """
        SELECT sent_time, destination_name, target_address, rtt_us, outcome
        FROM ping_measurements
        ORDER BY sent_time DESC
        LIMIT 5
    """

    with request_meta_context() as meta:
        try:
            latency_rows = client.query(latency_sql)
            health_rows = client.query(health_sql)
            recent_rows = client.query(recent_sql)
        except QuestDBError as exc:
            logger.warning("QuestDB overview query unavailable: %s", exc)
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        series_by_destination: dict[int, LatencySeriesSchema] = {}
        for row in latency_rows:
            if row.get("average_latency_ms") is None:
                continue
            destination_id = int(row["destination_id"])
            if destination_id not in series_by_destination:
                series_by_destination[destination_id] = LatencySeriesSchema(
                    destination_id=destination_id,
                    name=str(row["destination_name"]),
                    points=[],
                )
            series_by_destination[destination_id].points.append(
                LatencyPointSchema(timestamp=row["timestamp"], average_latency_ms=float(row["average_latency_ms"]))
            )
        latency_series = list(series_by_destination.values())
        destinations = []
        for row in health_rows:
            availability = float(row.get("availability_pct") or 0)
            latest_outcome = str(row.get("latest_outcome") or "unknown")
            destinations.append(
                DestinationHealthSchema(
                    destination_id=int(row["destination_id"]),
                    name=str(row["destination_name"]),
                    address=str(row.get("target_address") or "—"),
                    average_latency_ms=float(row["average_latency_ms"]) if row.get("average_latency_ms") is not None else None,
                    availability_pct=availability,
                    last_seen=row["last_seen"],
                    latest_outcome=latest_outcome,
                    status="Healthy" if latest_outcome == "reply" and availability >= 95 else "Degraded",
                )
            )

        all_latency_points = [point for series in latency_series for point in series.points]
        average_latency = (
            sum(point.average_latency_ms for point in all_latency_points) / len(all_latency_points) if all_latency_points else None
        )
        availability = (
            sum(destination.availability_pct for destination in destinations) / len(destinations) if destinations else None
        )
        recent_events = [
            PingEventSchema(
                timestamp=row["sent_time"],
                destination_name=str(row["destination_name"]),
                address=str(row.get("target_address") or "—"),
                latency_ms=float(row["rtt_us"]) / 1000 if row.get("rtt_us") is not None else None,
                outcome=str(row["outcome"]),
            )
            for row in recent_rows
        ]
        data = PingOverviewSchema(
            range_hours=hours,
            average_latency_ms=average_latency,
            availability_pct=availability,
            packet_loss_pct=100 - availability if availability is not None else None,
            latency_series=latency_series,
            destinations=destinations,
            recent_events=recent_events,
        )

    return ApiResponse(meta=build_meta(meta), data=data)
