package main

import (
	"context"
	"fmt"
	"testing"
	"time"
)

func TestWorkerManager(t *testing.T) {
	manager := NewWorkerManager()
	workersMax := 50

	for i := 0; i < workersMax; i++ {
		id := i
		err := manager.Start(id, func(ctx context.Context, worker *Worker) {
			ticker := time.NewTicker(time.Second)
			defer ticker.Stop()
			for {
				select {
				case <-ctx.Done():
					fmt.Println(id, ": stopping")
					return
				case <-ticker.C:
					fmt.Println(id, ": ping")
				}
			}
		})
		if err != nil {
			panic(err)
		}
	}

	// Let it run for a few seconds.
	time.Sleep(2 * time.Second)
	if count := manager.Count(); count != workersMax {
		t.Errorf("expected a total of %d workers, got %d", workersMax, count)
	}

	if count := manager.RunningCount(); count != workersMax {
		t.Errorf("expected running %d workers, got %d", workersMax, count)
	}

	fmt.Println(
		"Running:",
		manager.IsRunning(1),
		manager.IsRunning(2),
	)
	// Tell the goroutine to stop.
	fmt.Println("Requesting stop...")
	if err := manager.Stop(1); err != nil {
		panic(err)
	}

	// Wait for the goroutine to actually exit.
	if err := manager.Wait(1); err != nil {
		panic(err)
	}
	fmt.Println(
		"Running:",
		manager.IsRunning(1),
	)

	// Check that the goroutine actually stopped.
	if count := manager.Count(); count != workersMax {
		t.Errorf("expected a total of %d workers, got %d", workersMax, count)
	}

	if count := manager.RunningCount(); count != workersMax-1 {
		t.Errorf("expected running %d workers, got %d", workersMax-1, count)
	}

	// Remove the completed worker.
	if err := manager.Remove(1); err != nil {
		panic(err)
	}
	fmt.Println(
		"Workers:",
		manager.Count(),
	)
	time.Sleep(3 * time.Second)
}
