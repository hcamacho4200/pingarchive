package main

import "os"

type Settings struct {
	apiBindHost                    string `json:"api_bind_host"`
	apiBindPort                    string `json:"api_bind_port"`
	pingControlServerListenAddress string `json:"ping_control_server_listen_address"`
	qwestDBAddress                 string `json:"qwest_db_address"`
}

func NewSettings() *Settings {
	return &Settings{
		apiBindHost:                    getEnv("API_BIND_HOST", "localhost"),
		apiBindPort:                    getEnv("API_BIND_PORT", "8002"),
		pingControlServerListenAddress: getEnv("PING_CONTROL_SERVER_LISTEN_ADDRESS", "0.0.0.0:8100"),
		qwestDBAddress:                 getEnv("QWEST_DB_ADDRESS", "localhost:9000"),
	}
}

// getEnv returns the value of the environment variable if it exists, otherwise returns the default value
func getEnv(key string, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
