package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// Worker represents a running goroutine.

type Worker struct {
	ID     int
	name   string
	Done   chan struct{}
	Cancel context.CancelFunc

	mu        sync.RWMutex
	lastRunAt time.Time
}

// Running reports whether the worker's goroutine is still running.
func (w *Worker) Running() bool {
	select {
	case <-w.Done:
		return false
	default:
		return true
	}
}

func (w *Worker) LastRunAt() time.Time {
	w.mu.RLock()
	defer w.mu.RUnlock()
	return w.lastRunAt
}

func (w *Worker) SetLastRunAt(t time.Time) {
	w.mu.Lock()
	defer w.mu.Unlock()
	w.lastRunAt = t
}

// WorkerManager keeps track of running workers.
type WorkerManager struct {
	mu      sync.RWMutex
	workers map[int]*Worker
}

// NewWorkerManager creates an initialized WorkerManager.

func NewWorkerManager() *WorkerManager {
	return &WorkerManager{
		workers: make(map[int]*Worker),
	}

}

// Start creates and starts a new worker.
func (m *WorkerManager) Start(
	id int,
	fn func(ctx context.Context, worker *Worker),
) error {
	m.mu.Lock()
	// Don't allow duplicate workers with the same ID.
	if worker, exists := m.workers[id]; exists && worker.Running() {
		m.mu.Unlock()
		return fmt.Errorf("worker %d is already running", id)
	}
	ctx, cancel := context.WithCancel(context.Background())
	worker := &Worker{
		ID:     id,
		Done:   make(chan struct{}),
		Cancel: cancel,
	}
	worker.name = fmt.Sprintf("worker-%d", id)
	m.workers[id] = worker
	m.mu.Unlock()
	go func() {
		defer close(worker.Done)
		fn(ctx, worker)
	}()
	return nil
}

// Get returns a worker by ID.

func (m *WorkerManager) Get(id int) (*Worker, bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	worker, exists := m.workers[id]
	return worker, exists

}

// IsRunning reports whether a worker exists and is currently running.
func (m *WorkerManager) IsRunning(id int) bool {
	m.mu.RLock()
	defer m.mu.RUnlock()
	worker, exists := m.workers[id]
	if !exists {
		return false
	}
	return worker.Running()
}

// Stops a worker.
func (m *WorkerManager) Stop(id int) error {
	m.mu.RLock()
	worker, exists := m.workers[id]
	m.mu.RUnlock()
	if !exists {
		return fmt.Errorf("worker %d does not exist", id)
	}
	worker.Cancel()
	return nil

}

// Stop all workers
func (m *WorkerManager) StopAll() error {
	m.mu.RLock()
	defer m.mu.RUnlock()
	for _, worker := range m.workers {
		if worker.Running() {
			worker.Cancel()
		}
	}
	return nil
}

// Wait waits for a worker to finish.
func (m *WorkerManager) Wait(id int) error {

	m.mu.RLock()
	worker, exists := m.workers[id]
	m.mu.RUnlock()
	if !exists {
		return fmt.Errorf("worker %d does not exist", id)
	}
	<-worker.Done
	return nil
}

func (m *WorkerManager) Remove(id int) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	worker, exists := m.workers[id]
	if !exists {
		return fmt.Errorf("worker %d does not exist", id)
	}
	if worker.Running() {
		return fmt.Errorf("worker %d is still running", id)
	}
	delete(m.workers, id)
	return nil

}

// Count returns the number of workers currently registered.
func (m *WorkerManager) Count() int {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return len(m.workers)
}

// RunningCount returns the number of workers currently running.
func (m *WorkerManager) RunningCount() int {
	m.mu.RLock()
	defer m.mu.RUnlock()
	count := 0
	for _, worker := range m.workers {
		if worker.Running() {
			count++
		}
	}
	return count
}

func (m *WorkerManager) List() []Worker {
	m.mu.RLock()
	defer m.mu.RUnlock()
	results := make([]Worker, 0, len(m.workers))

	for _, worker := range m.workers {
		results = append(results, *worker)
	}
	return results
}

func (m *WorkerManager) Range(fn func(int, *Worker) bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	for id, worker := range m.workers {
		if !fn(id, worker) {
			return
		}
	}
}

