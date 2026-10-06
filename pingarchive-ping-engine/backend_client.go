package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

type BackendClient struct {
	baseURL string
	client  *http.Client
}

func NewBackendClient(baseURL string) *BackendClient {
	return &BackendClient{
		baseURL: baseURL,
		client: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

type PingDestinationResponse struct {
	Data []PingDestination `json:"data"`
}

func (c *BackendClient) GetPingDestinations() ([]PingDestination, error) {

	path := c.baseURL + "/api/v1/ping_destinations"
	resp, err := c.client.Get(path)
	if err != nil {
		return nil, fmt.Errorf("getting ping destinations: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf(
			"getting ping destinations: unexpected HTTP status %s",
			resp.Status,
		)
	}
	var response PingDestinationResponse
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		return nil, fmt.Errorf("decoding ping destinations: %w", err)
	}

	return response.Data, nil
}
