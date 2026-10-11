package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"time"
)

type ControlServer struct {
	manager        *WorkerManager
	pingStats      *PingStats
	listenAddress  string
	cancelMain     context.CancelFunc
	restartWorkers func() (int, error)
}

func NewControlServer(cancelMain context.CancelFunc, manager *WorkerManager, pingStats *PingStats, listenAddress string, restartWorkers func() (int, error)) *ControlServer {
	return &ControlServer{
		manager:        manager,
		listenAddress:  listenAddress,
		pingStats:      pingStats,
		cancelMain:     cancelMain,
		restartWorkers: restartWorkers,
	}
}

type APIResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
	Data    any    `json:"data"`
}

func (s *ControlServer) Start() error {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /health", s.health)
	mux.HandleFunc("GET /ping_stats", s.handleStats)
	mux.HandleFunc("GET /workers", s.workers)
	mux.HandleFunc("POST /restart", s.restart)
	mux.HandleFunc("GET /cancel_main", s.handleCancelMain)

	// mux.HandleFunc("POST /workers/{id}/stop", s.stopWorker)

	server := &http.Server{
		Addr:              s.listenAddress,
		Handler:           mux,
		ReadHeaderTimeout: 5 * time.Second,
	}
	log.Printf("PingArchive control API listening on %s", s.listenAddress)
	return server.ListenAndServe()
}

func (s *ControlServer) restart(w http.ResponseWriter, r *http.Request) {
	if s.restartWorkers == nil {
		writeJSON(w, http.StatusNotImplemented, APIResponse{
			Success: false,
			Message: "Worker restart is not configured",
		})
		return
	}

	workers, err := s.restartWorkers()
	if err != nil {
		log.Printf("unable to restart ping workers: %v", err)
		writeJSON(w, http.StatusBadGateway, APIResponse{
			Success: false,
			Message: err.Error(),
		})
		return
	}

	writeJSON(w, http.StatusOK, APIResponse{
		Success: true,
		Message: "Ping workers restarted",
		Data: map[string]int{
			"workers": workers,
		},
	})
}

func (s *ControlServer) health(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, APIResponse{
		Success: true,
		Message: "PingArchive engine is running",
	})
}

func (s *ControlServer) workers(w http.ResponseWriter, r *http.Request) {
	type data struct {
		ID        int       `json:"id"`
		Name      string    `json:"name"`
		LastRunAt time.Time `json:"last_run_at"`
	}

	results := make([]data, 0, len(s.manager.List()))
	s.manager.Range(func(_ int, worker *Worker) bool {
		results = append(results, data{
			ID:        worker.ID,
			Name:      worker.name,
			LastRunAt: worker.LastRunAt(),
		})
		return true
	})

	writeJSON(w, http.StatusOK, APIResponse{
		Success: true,
		Message: "Success",
		Data:    results,
	})
}

func (s *ControlServer) handleStats(w http.ResponseWriter, r *http.Request) {
	type data struct {
		SuccessCount int `json:"success_count"`
		FailureCount int `json:"failure_count"`
		SkippedCount int `json:"skipped_count"`
		TimeoutCount int `json:"timeout_count"`
	}

	results := data{
		SuccessCount: s.pingStats.SuccessCount,
		FailureCount: s.pingStats.FailureCount,
		SkippedCount: s.pingStats.SkippedCount,
		TimeoutCount: s.pingStats.TimeoutCount,
	}
	writeJSON(w, http.StatusOK, APIResponse{
		Success: true,
		Message: "Success",
		Data:    results,
	})
}

func (s *ControlServer) handleCancelMain(w http.ResponseWriter, r *http.Request) {
	s.cancelMain()
	type data struct {
		SuccessCount int `json:"success_count"`
		FailureCount int `json:"failure_count"`
		SkippedCount int `json:"skipped_count"`
		TimeoutCount int `json:"timeout_count"`
	}

	results := data{
		SuccessCount: s.pingStats.SuccessCount,
		FailureCount: s.pingStats.FailureCount,
		SkippedCount: s.pingStats.SkippedCount,
		TimeoutCount: s.pingStats.TimeoutCount,
	}
	writeJSON(w, http.StatusOK, APIResponse{
		Success: true,
		Message: "Success",
		Data:    results,
	})
}

func writeJSON(w http.ResponseWriter, status int, value any) {

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(value); err != nil {
		log.Printf("unable to encode response: %v", err)
	}
}
