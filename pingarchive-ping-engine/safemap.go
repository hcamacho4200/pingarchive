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

func (s *SafeMap[K, V]) Remove(key K) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.m, key)
}

// Keys returns all keys currently in the map.
func (s *SafeMap[K, V]) Keys() []K {

	s.mu.RLock()
	defer s.mu.RUnlock()
	keys := make([]K, 0, len(s.m))
	for key := range s.m {
		keys = append(keys, key)
	}
	return keys
}

// Range calls fn for each key/value pair in the map.
// Returning false from fn stops iteration.
func (s *SafeMap[K, V]) Range(fn func(K, V) bool) {

	s.mu.RLock()
	defer s.mu.RUnlock()
	for key, value := range s.m {
		if !fn(key, value) {
			return
		}
	}
}
