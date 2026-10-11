package main

import (
	"context"
	"errors"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestControlServerRestart(t *testing.T) {
	server := NewControlServer(func() {}, NewWorkerManager(), NewPingStats(), "127.0.0.1:0", func() (int, error) {
		return 3, nil
	})
	recorder := httptest.NewRecorder()
	request := httptest.NewRequest(http.MethodPost, "/restart", nil)

	server.restart(recorder, request)

	if recorder.Code != http.StatusOK {
		t.Fatalf("expected status %d, got %d", http.StatusOK, recorder.Code)
	}
	if !strings.Contains(recorder.Body.String(), `"workers":3`) {
		t.Fatalf("expected worker count in response, got %s", recorder.Body.String())
	}
}

func TestControlServerRestartFailure(t *testing.T) {
	server := NewControlServer(context.CancelFunc(func() {}), NewWorkerManager(), NewPingStats(), "127.0.0.1:0", func() (int, error) {
		return 0, errors.New("backend unavailable")
	})
	recorder := httptest.NewRecorder()
	request := httptest.NewRequest(http.MethodPost, "/restart", nil)

	server.restart(recorder, request)

	if recorder.Code != http.StatusBadGateway {
		t.Fatalf("expected status %d, got %d", http.StatusBadGateway, recorder.Code)
	}
	if !strings.Contains(recorder.Body.String(), "backend unavailable") {
		t.Fatalf("expected restart error in response, got %s", recorder.Body.String())
	}
}
