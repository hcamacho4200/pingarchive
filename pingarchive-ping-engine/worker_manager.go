package main

import (
	"context"
	"fmt"
	"sync"
)

// Worker represents a running goroutine.

type Worker struct {
	ID     string
	Done   chan struct{}
	Cancel context.CancelFunc
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

// WorkerManager keeps track of running workers.

type WorkerManager struct {
	mu      sync.RWMutex
	workers map[string]*Worker
}

// NewWorkerManager creates an initialized WorkerManager.

func NewWorkerManager() *WorkerManager {

	return &WorkerManager{
		workers: make(map[string]*Worker),
	}

}

// Start creates and starts a new worker.

//

// The supplied function receives a context that will be cancelled

// when Stop() is called.

func (m *WorkerManager) Start(

	id string,
	fn func(ctx context.Context),

) error {

	m.mu.Lock()
	// Don't allow duplicate workers with the same ID.
	if worker, exists := m.workers[id]; exists && worker.Running() {
		m.mu.Unlock()
		return fmt.Errorf("worker %q is already running", id)
	}
	ctx, cancel := context.WithCancel(context.Background())
	worker := &Worker{
		ID:     id,
		Done:   make(chan struct{}),
		Cancel: cancel,
	}
	m.workers[id] = worker
	m.mu.Unlock()
	go func() {
		defer close(worker.Done)
		fn(ctx)
	}()
	return nil

}

// Get returns a worker by ID.

func (m *WorkerManager) Get(id string) (*Worker, bool) {

	m.mu.RLock()
	defer m.mu.RUnlock()
	worker, exists := m.workers[id]
	return worker, exists

}

// IsRunning reports whether a worker exists and is currently running.

func (m *WorkerManager) IsRunning(id string) bool {

	m.mu.RLock()
	defer m.mu.RUnlock()
	worker, exists := m.workers[id]
	if !exists {
		return false
	}
	return worker.Running()

}

func (m *WorkerManager) Stop(id string) error {

	m.mu.RLock()
	worker, exists := m.workers[id]
	m.mu.RUnlock()
	if !exists {
		return fmt.Errorf("worker %q does not exist", id)
	}
	worker.Cancel()
	return nil

}

// Wait waits for a worker to finish.

func (m *WorkerManager) Wait(id string) error {

	m.mu.RLock()
	worker, exists := m.workers[id]
	m.mu.RUnlock()
	if !exists {
		return fmt.Errorf("worker %q does not exist", id)
	}
	<-worker.Done
	return nil

}

func (m *WorkerManager) Remove(id string) error {

	m.mu.Lock()
	defer m.mu.Unlock()
	worker, exists := m.workers[id]
	if !exists {
		return fmt.Errorf("worker %q does not exist", id)
	}
	if worker.Running() {
		return fmt.Errorf("worker %q is still running", id)
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
