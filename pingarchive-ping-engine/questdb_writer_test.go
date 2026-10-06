package main

import (
	"context"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"
	"time"
)

func TestQuestDBWriterCreatesSchemaAndWritesPing(t *testing.T) {
	var mutex sync.Mutex
	var schemaQuery string
	var writtenRows string

	server := httptest.NewServer(http.HandlerFunc(func(response http.ResponseWriter, request *http.Request) {
		mutex.Lock()
		defer mutex.Unlock()

		switch request.URL.Path {
		case "/api/v1/sql/execute":
			schemaQuery = request.URL.Query().Get("query")
			response.Header().Set("Content-Type", "application/json")
			_, _ = response.Write([]byte(`{"ddl":"OK"}`))
		case "/write", "/api/v2/write":
			body, err := io.ReadAll(request.Body)
			if err != nil {
				t.Errorf("read QuestDB request: %v", err)
			}
			writtenRows += string(body)
			response.WriteHeader(http.StatusNoContent)
		default:
			http.NotFound(response, request)
		}
	}))
	defer server.Close()

	writer, err := NewQuestDBWriter(context.Background(), server.URL)
	if err != nil {
		t.Fatalf("create writer: %v", err)
	}

	sentAt := time.Date(2026, time.October, 5, 12, 0, 0, 123456000, time.UTC)
	receivedAt := sentAt.Add(18 * time.Millisecond)
	measurement := PingData{
		id:              321,
		destinationID:   42,
		destinationName: "google-dns",
		target:          net.ParseIP("8.8.8.8"),
		source:          &net.IPAddr{IP: net.ParseIP("8.8.8.8")},
		sequence:        7,
		sentAt:          sentAt,
		receivedAt:      receivedAt,
		rtt:             receivedAt.Sub(sentAt),
	}

	if err := writer.WritePing(context.Background(), measurement, "reply"); err != nil {
		t.Fatalf("write measurement: %v", err)
	}
	if err := writer.Close(context.Background()); err != nil {
		t.Fatalf("close writer: %v", err)
	}

	mutex.Lock()
	defer mutex.Unlock()
	if !strings.Contains(schemaQuery, "TIMESTAMP(sent_time)") || !strings.Contains(schemaQuery, "destination_id LONG") {
		t.Fatalf("unexpected schema query: %s", schemaQuery)
	}
	for _, expected := range []string{
		"ping_measurements,destination_name=google-dns,outcome=reply",
		"destination_id=42i",
		"sequence=7i",
		"worker_id=321i",
		"rtt_us=18000i",
	} {
		if !strings.Contains(writtenRows, expected) {
			t.Errorf("expected ILP output to contain %q; got %q", expected, writtenRows)
		}
	}
}
