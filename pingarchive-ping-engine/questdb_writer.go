package main

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"

	qdb "github.com/questdb/go-questdb-client/v4"
)

const (
	pingMeasurementsTable = "ping_measurements"
	pingMeasurementsDDL   = `CREATE TABLE IF NOT EXISTS ping_measurements (
sent_time TIMESTAMP,
destination_id LONG,
destination_name SYMBOL CAPACITY 256 CACHE,
received_time TIMESTAMP,
rtt_us LONG,
outcome SYMBOL CAPACITY 8 CACHE,
sequence LONG,
worker_id LONG,
target_address VARCHAR,
source_address VARCHAR,
error_message VARCHAR
) TIMESTAMP(sent_time)
PARTITION BY DAY
DEDUP UPSERT KEYS (sent_time, destination_id, worker_id, sequence)`
)

type PingMeasurementWriter interface {
	WritePing(context.Context, PingData, string) error
	Close(context.Context) error
}

type QuestDBWriter struct {
	sender qdb.LineSender
}

func NewQuestDBWriter(ctx context.Context, address string) (*QuestDBWriter, error) {
	normalizedAddress := normalizeQuestDBAddress(address)
	if err := ensurePingMeasurementsTable(ctx, normalizedAddress); err != nil {
		return nil, err
	}

	sender, err := qdb.NewLineSender(
		ctx,
		qdb.WithHttp(),
		qdb.WithAddress(normalizedAddress),
		qdb.WithAutoFlushInterval(time.Second),
	)
	if err != nil {
		return nil, fmt.Errorf("create QuestDB sender: %w", err)
	}

	return &QuestDBWriter{sender: sender}, nil
}

func (writer *QuestDBWriter) WritePing(ctx context.Context, data PingData, outcome string) error {
	row := writer.sender.
		Table(pingMeasurementsTable).
		Symbol("destination_name", data.destinationName).
		Symbol("outcome", outcome).
		Int64Column("destination_id", int64(data.destinationID)).
		Int64Column("sequence", int64(data.sequence)).
		Int64Column("worker_id", int64(data.id)).
		StringColumn("target_address", data.target.String())

	if !data.receivedAt.IsZero() {
		row = row.
			TimestampColumn("received_time", data.receivedAt).
			Int64Column("rtt_us", data.rtt.Microseconds())
	}
	if data.source != nil {
		row = row.StringColumn("source_address", data.source.String())
	}
	if data.err != nil {
		row = row.StringColumn("error_message", data.err.Error())
	}

	if err := row.At(ctx, data.sentAt); err != nil {
		return fmt.Errorf("write ping measurement: %w", err)
	}
	return nil
}

func (writer *QuestDBWriter) Close(ctx context.Context) error {
	flushErr := writer.sender.Flush(ctx)
	closeErr := writer.sender.Close(ctx)
	if flushErr != nil || closeErr != nil {
		var closeErrors []error
		if flushErr != nil {
			closeErrors = append(closeErrors, fmt.Errorf("flush QuestDB sender: %w", flushErr))
		}
		if closeErr != nil {
			closeErrors = append(closeErrors, fmt.Errorf("close QuestDB sender: %w", closeErr))
		}
		return errors.Join(closeErrors...)
	}
	return nil
}

func normalizeQuestDBAddress(address string) string {
	address = strings.TrimSpace(address)
	address = strings.TrimPrefix(address, "http://")
	address = strings.TrimPrefix(address, "https://")
	return strings.TrimRight(address, "/")
}

func ensurePingMeasurementsTable(ctx context.Context, address string) error {
	endpoint := url.URL{
		Scheme: "http",
		Host:   address,
		Path:   "/api/v1/sql/execute",
	}
	query := endpoint.Query()
	query.Set("query", pingMeasurementsDDL)
	endpoint.RawQuery = query.Encode()

	request, err := http.NewRequestWithContext(ctx, http.MethodGet, endpoint.String(), nil)
	if err != nil {
		return fmt.Errorf("create QuestDB schema request: %w", err)
	}

	response, err := http.DefaultClient.Do(request)
	if err != nil {
		return fmt.Errorf("ensure QuestDB schema: %w", err)
	}
	defer response.Body.Close()

	if response.StatusCode < http.StatusOK || response.StatusCode >= http.StatusMultipleChoices {
		body, _ := io.ReadAll(io.LimitReader(response.Body, 4096))
		return fmt.Errorf("ensure QuestDB schema: HTTP %s: %s", response.Status, strings.TrimSpace(string(body)))
	}
	return nil
}
