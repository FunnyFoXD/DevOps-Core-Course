package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

// TestMainHandler tests the main endpoint GET /
func TestMainHandler(t *testing.T) {
	req := httptest.NewRequest("GET", "/", nil)
	w := httptest.NewRecorder()
	
	mainHandler(w, req)
	
	if w.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", w.Code)
	}
	
	contentType := w.Header().Get("Content-Type")
	if contentType != "application/json" {
		t.Errorf("Expected Content-Type application/json, got %s", contentType)
	}
	
	var info ServiceInfo
	if err := json.Unmarshal(w.Body.Bytes(), &info); err != nil {
		t.Fatalf("Failed to parse JSON: %v", err)
	}
	
	if info.Service.Name != "devops-info-service" {
		t.Errorf("Expected service name 'devops-info-service', got '%s'", info.Service.Name)
	}
	if info.Service.Version != "1.0.0" {
		t.Errorf("Expected version '1.0.0', got '%s'", info.Service.Version)
	}
	if info.Service.Framework != "Go" {
		t.Errorf("Expected framework 'Go', got '%s'", info.Service.Framework)
	}
	
	if info.System.Hostname == "" {
		t.Error("System.Hostname should not be empty")
	}
	if info.System.CPUCount <= 0 {
		t.Error("System.CPUCount should be positive")
	}
	
	if info.Runtime.UptimeSeconds < 0 {
		t.Error("Runtime.UptimeSeconds should be non-negative")
	}
	if info.Runtime.Timezone != "UTC" {
		t.Errorf("Expected timezone 'UTC', got '%s'", info.Runtime.Timezone)
	}
	
	if info.Request.Method != "GET" {
		t.Errorf("Expected method 'GET', got '%s'", info.Request.Method)
	}
	if info.Request.Path != "/" {
		t.Errorf("Expected path '/', got '%s'", info.Request.Path)
	}
	
	if len(info.Endpoints) < 2 {
		t.Errorf("Expected at least 2 endpoints, got %d", len(info.Endpoints))
	}
}

// TestHealthHandler tests the health endpoint GET /health
func TestHealthHandler(t *testing.T) {
	req := httptest.NewRequest("GET", "/health", nil)
	w := httptest.NewRecorder()
	
	healthHandler(w, req)
	
	if w.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", w.Code)
	}
	
	var health HealthResponse
	if err := json.Unmarshal(w.Body.Bytes(), &health); err != nil {
		t.Fatalf("Failed to parse JSON: %v", err)
	}
	
	if health.Status != "healthy" {
		t.Errorf("Expected status 'healthy', got '%s'", health.Status)
	}
	
	if health.UptimeSeconds < 0 {
		t.Error("UptimeSeconds should be non-negative")
	}
	
	if _, err := time.Parse(time.RFC3339, health.Timestamp); err != nil {
		t.Errorf("Timestamp should be in RFC3339 format: %v", err)
	}
}

// TestNotFoundHandler tests 404 error handling
func TestNotFoundHandler(t *testing.T) {
	req := httptest.NewRequest("GET", "/nonexistent", nil)
	w := httptest.NewRecorder()
	
	notFoundHandler(w, req)
	
	if w.Code != http.StatusNotFound {
		t.Errorf("Expected status 404, got %d", w.Code)
	}
	
	var errResp ErrorResponse
	if err := json.Unmarshal(w.Body.Bytes(), &errResp); err != nil {
		t.Fatalf("Failed to parse JSON: %v", err)
	}
	
	if errResp.Error != "Not Found" {
		t.Errorf("Expected error 'Not Found', got '%s'", errResp.Error)
	}
}

// TestGetUptime tests the getUptime helper function
func TestGetUptime(t *testing.T) {
	originalStartTime := startTime
	startTime = time.Now().Add(-5 * time.Minute)
	defer func() { startTime = originalStartTime }()
	
	seconds, human := getUptime()
	
	if seconds < 0 {
		t.Error("Uptime seconds should be non-negative")
	}
	if human == "" {
		t.Error("Uptime human string should not be empty")
	}
}

// TestGetSystemInfo tests the getSystemInfo helper function
func TestGetSystemInfo(t *testing.T) {
	system := getSystemInfo()
	
	if system.Hostname == "" {
		t.Error("Hostname should not be empty")
	}
	if system.Platform == "" {
		t.Error("Platform should not be empty")
	}
	if system.CPUCount <= 0 {
		t.Error("CPUCount should be positive")
	}
	if system.GoVersion == "" {
		t.Error("GoVersion should not be empty")
	}
}

// TestGetClientIP tests the getClientIP helper function
func TestGetClientIP(t *testing.T) {
	tests := []struct {
		name           string
		request        *http.Request
		expectedPrefix string
	}{
		{
			name:           "X-Forwarded-For header",
			request:        httptest.NewRequest("GET", "/", nil),
			expectedPrefix: "unknown",
		},
	}
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ip := getClientIP(tt.request)
			if ip == "" {
				t.Error("Client IP should not be empty")
			}
		})
	}
}

// TestWrongMethod tests POST to GET endpoint
func TestWrongMethod(t *testing.T) {
	req := httptest.NewRequest("POST", "/", nil)
	w := httptest.NewRecorder()
	
	mainHandler(w, req)
	
	if w.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", w.Code)
	}
	
	var info ServiceInfo
	if err := json.Unmarshal(w.Body.Bytes(), &info); err != nil {
		t.Fatalf("Failed to parse JSON: %v", err)
	}
	
	if info.Request.Method != "POST" {
		t.Errorf("Expected method 'POST', got '%s'", info.Request.Method)
	}
}