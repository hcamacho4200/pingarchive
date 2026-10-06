package main

type PingDestination struct {
	ID           int    `json:"id"`
	Name         string `json:"name"`
	IPv4         string `json:"ipv4"`
	IPv6         string `json:"ipv6"`
	Host         string `json:"host"`
	LocationZone string `json:"location_zone"`
	AddressType  string `json:"address_type"`
	PingInterval int    `json:"ping_interval"`
	Enabled      bool   `json:"enabled"`
}
