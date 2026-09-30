package main

import "sync"

type SafeMap[K comparable, V any] struct {
	mu sync.RWMutex
	m  map[K]V
}

// NewSafeMap initializes and returns a ready-to-use SafeMap.
func NewSafeMap[K comparable, V any]() *SafeMap[K, V] {
	return &SafeMap[K, V]{
		m: make(map[K]V),
	}
}

func (s *SafeMap[K, V]) Get(key K) (V, bool) {
	s.mu.RLock() // Multiple readers can hold a Read Lock
	defer s.mu.RUnlock()
	val, ok := s.m[key]
	return val, ok
}

func (s *SafeMap[K, V]) Set(key K, val V) {
	s.mu.Lock() // Only one writer can hold a Lock
	defer s.mu.Unlock()
	s.m[key] = val
}
