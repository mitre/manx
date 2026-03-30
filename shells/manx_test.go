package main

import (
	"testing"
)

func TestBuildProfileServerIsHTTP(t *testing.T) {
	socketAddr := "0.0.0.0:5678"
	httpServer := "http://localhost:8888"
	executors := []string{"sh"}

	profile := buildProfile(socketAddr, httpServer, executors)

	server, ok := profile["server"]
	if !ok {
		t.Fatal("profile missing 'server' key")
	}
	if server != httpServer {
		t.Errorf("expected profile['server'] = %q, got %q", httpServer, server)
	}
}

func TestBuildProfileServerNotSocket(t *testing.T) {
	socketAddr := "10.0.0.1:7777"
	httpServer := "https://caldera.example.com:8443"
	executors := []string{"psh", "cmd"}

	profile := buildProfile(socketAddr, httpServer, executors)

	server := profile["server"].(string)
	if server == socketAddr {
		t.Error("profile['server'] should be the HTTP URL, not the TCP socket address")
	}
	if server != httpServer {
		t.Errorf("expected profile['server'] = %q, got %q", httpServer, server)
	}
}

func TestBuildProfileContainsRequiredFields(t *testing.T) {
	profile := buildProfile("0.0.0.0:5678", "http://localhost:8888", nil)

	requiredFields := []string{
		"server", "host", "username", "architecture",
		"platform", "location", "pid", "ppid", "executors", "exe_name",
	}
	for _, field := range requiredFields {
		if _, ok := profile[field]; !ok {
			t.Errorf("profile missing required field %q", field)
		}
	}
}
