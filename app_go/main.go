package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"runtime"
	"time"
)

// Error response structure
type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message"`
}

// Service metadata
type Service struct {
	Name        string `json:"name"`
	Version     string `json:"version"`
	Description string `json:"description"`
	Framework   string `json:"framework"`
}

// System information
type System struct {
	Hostname        string `json:"hostname"`
	Platform        string `json:"platform"`
	PlatformVersion string `json:"platform_version"`
	Architecture    string `json:"architecture"`
	CPUCount        int    `json:"cpu_count"`
	GoVersion       string `json:"go_version"`
}

// Runtime information
type Runtime struct {
	UptimeSeconds int    `json:"uptime_seconds"`
	UptimeHuman   string `json:"uptime_human"`
	CurrentTime   string `json:"current_time"`
	Timezone      string `json:"timezone"`
}

// Request information
type Request struct {
	ClientIP  string `json:"client_ip"`
	UserAgent string `json:"user_agent"`
	Method    string `json:"method"`
	Path      string `json:"path"`
}

// Endpoint information
type Endpoint struct {
	Path        string `json:"path"`
	Method      string `json:"method"`
	Description string `json:"description"`
}

// Main service info
type ServiceInfo struct {
	Service   Service    `json:"service"`
	System    System     `json:"system"`
	Runtime   Runtime    `json:"runtime"`
	Request   Request    `json:"request"`
	Endpoints []Endpoint `json:"endpoints"`
}

// Health check response
type HealthResponse struct {
	Status        string `json:"status"`
	Timestamp     string `json:"timestamp"`
	UptimeSeconds int    `json:"uptime_seconds"`
}

var startTime = time.Now()

// getSystemInfo return main system information
func getSystemInfo() System {
	hostname, _ := os.Hostname()

	return System{
		Hostname:        hostname,
		Platform:        runtime.GOOS,
		PlatformVersion: runtime.GOOS + " " + runtime.GOARCH,
		Architecture:    runtime.GOARCH,
		CPUCount:        runtime.NumCPU(),
		GoVersion:       runtime.Version(),
	}
}

// getUptime calculate uptime
func getUptime() (int, string) {
	delta := time.Since(startTime)
	totalSeconds := int(delta.Seconds())
	hours := totalSeconds / 3600
	minutes := (totalSeconds % 3600) / 60

	hoursStr := "hours"
	if hours == 1 {
		hoursStr = "hour"
	}
	minutesStr := "minutes"
	if minutes == 1 {
		minutesStr = "minute"
	}

	human := fmt.Sprintf("%d %s, %d %s", hours, hoursStr, minutes, minutesStr)

	return totalSeconds, human
}

func getClientIP(r *http.Request) string {
	// Check X-Forwarded-For
	if ip := r.Header.Get("X-Forwarded-For"); ip != "" {
		return ip
	}

	// Check X-Real-IP
	if ip := r.Header.Get("X-Real-IP"); ip != "" {
		return ip
	}

	// Fallback to RemoteAddr
	if ip := r.RemoteAddr; ip != "" {
		host, _, err := net.SplitHostPort(ip)
		if err != nil {
			// Try to parse as IP without port
			host = ip
		}

		// Convert IPv6 localhost to IPv4 for consistency
		if host == "::1" || host == "[::1]" {
			return "127.0.0.1"
		}

		return host
	}

	return "unknown"
}

// NotFound handler for 404 errors
func notFoundHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNotFound)

	response := ErrorResponse{
		Error:   "Not Found",
		Message: "Endpoint does not exist",
	}

	if err := json.NewEncoder(w).Encode(response); err != nil {
		log.Printf("Error encoding JSON: %v", err)
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
		return
	}
}

// Main endpoint handler
func mainHandler(w http.ResponseWriter, r *http.Request) {
	uptimeSeconds, uptimeHuman := getUptime()

	userAgent := r.Header.Get("User-Agent")
	if userAgent == "" {
		userAgent = "unknown"
	}

	info := ServiceInfo{
		Service: Service{
			Name:        "devops-info-service",
			Version:     "1.0.0",
			Description: "DevOps course info service",
			Framework:   "Go",
		},
		System: getSystemInfo(),
		Runtime: Runtime{
			UptimeSeconds: uptimeSeconds,
			UptimeHuman:   uptimeHuman,
			CurrentTime:   time.Now().UTC().Format(time.RFC3339),
			Timezone:      "UTC",
		},
		Request: Request{
			ClientIP:  getClientIP(r),
			UserAgent: userAgent,
			Method:    r.Method,
			Path:      r.URL.Path,
		},
		Endpoints: []Endpoint{
			{Path: "/", Method: "GET", Description: "Service information"},
			{Path: "/health", Method: "GET", Description: "Health check"},
		},
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(info); err != nil {
		log.Printf("Error encoding JSON: %v", err)
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
		return
	}
}

// Health check handler
func healthHandler(w http.ResponseWriter, r *http.Request) {
	uptimeSeconds, _ := getUptime()

	response := HealthResponse{
		Status:        "healthy",
		Timestamp:     time.Now().UTC().Format(time.RFC3339),
		UptimeSeconds: uptimeSeconds,
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(response); err != nil {
		log.Printf("Error encoding JSON: %v", err)
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
		return
	}
}

func main() {
	// Registers handlers
	http.HandleFunc("/health", healthHandler)

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/" {
			mainHandler(w, r)
		} else {
			notFoundHandler(w, r)
		}
	})

	// Get port and host from env variable
	host := os.Getenv("HOST")
	if host == "" {
		host = "0.0.0.0"
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "5000"
	}

	// Start application
	addr := host + ":" + port

	log.Printf("Starting DevOps Info Service on %s", addr)
	if err := http.ListenAndServe(addr, nil); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}
