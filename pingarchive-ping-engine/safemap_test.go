package main

import "testing"

func TestSafeMapSetGet(t *testing.T) {
	sm := NewSafeMap[string, int]()
	sm.Set("foo", 1)
	sm.Set("bar", 2)

	if v, ok := sm.Get("foo"); !ok || v != 1 {
		t.Errorf("expected foo to be 1, got %v", v)
	}
	if v, ok := sm.Get("bar"); !ok || v != 2 {
		t.Errorf("expected bar to be 2, got %v", v)
	}
}
