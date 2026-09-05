package main

import "time"

// fetchRows is the real data source; tests inject their own.
func fetchRows() ([]Row, error) {
	return []Row{
		{Name: "alpha", Status: "ready", UpdatedAt: time.Date(2026, 8, 1, 9, 0, 0, 0, time.UTC)},
		{Name: "beta", Status: "stale", UpdatedAt: time.Date(2026, 7, 15, 12, 30, 0, 0, time.UTC)},
	}, nil
}
