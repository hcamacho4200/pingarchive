package main

import "sync"

type PingStats struct {
	SuccessCount int `json:"success"`
	FailureCount int `json:"failure"`
	SkippedCount int `json:"skipped"`
	TimeoutCount int `json:"timeout"`
	mu           sync.Mutex
}

// NewPingStats
func NewPingStats() *PingStats {
	return &PingStats{}
}

func (p *PingStats) IncrementSuccess() {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.SuccessCount++
}

func (p *PingStats) IncrementFailure() {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.FailureCount++
}

func (p *PingStats) IncrementSkipped() {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.SkippedCount++
}

func (p *PingStats) IncrementTimeout() {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.TimeoutCount++
}
