package main

import (
	"errors"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/golang/glog"
)

// A vault server which maintains a list of vaults which will store the data (value).
// We only store positive values.
type VaultServer struct {
	mux   *http.ServeMux
	port  int
	value int
}

// Create and return a new Control server instance.
// Provide the port on which we will listen.
// We store the port of the vault and not the controller, since the port is how we will
// distinguish the vaults in the logs when run via `docker-compose up`
func NewVaultServer(port int) *VaultServer {
	s := new(VaultServer)
	s.mux = http.NewServeMux()
	s.value = 0
	s.port = port
	s.mux.HandleFunc("/", s.handle)
	http.DefaultClient.Timeout = time.Second
	return s
}

// Handle GET and POST requests to the root path.
func (s *VaultServer) handle(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		// We only support operations on the root path.
		http.NotFound(w, r)
		return
	}
	if r.Method == http.MethodGet {
		s.get(w, r)
	} else if r.Method == http.MethodPost {
		s.post(w, r)
	} else {
		// Do not support PATCH, DELETE, etc, operations.
		http.NotFound(w, r)
	}
}

// Return the value stored in the vault. This should always be a success.
func (s *VaultServer) get(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(fmt.Sprintf("%d", s.value)))
}

// Update the value stored in the vault.
// Logs a warning if the value decreases for whatever reason (but still update it).
func (s *VaultServer) post(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		// Make sure we actually get a valid body from the client.
		glog.Warningf("Could not read body: %v\n", err)
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("Invalid or missing POST body"))
		return
	}
	v := string(body)
	n, e := strconv.Atoi(v)
	if n >= 0 && e == nil {
		// We only store positive values.
		if n < s.value {
			glog.Warningf("THIS SHOULD NEVER HAPPEN: Counter value regressed from %d to %d", s.value, n)
		}
		s.value = n
		glog.Infof("Set Vault :%d Counter %d", s.port, s.value)
		w.WriteHeader(http.StatusOK)
		w.Write(body)
	} else {
		// Either the body was not a valid integer, or it was negative.
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("Invalid or missing POST body"))
	}
}


func main() {
	portPtr := flag.Int("port", 8001, "Port on which to listen for requests")
	flag.Parse()
	s := NewVaultServer(*portPtr)
	err := http.ListenAndServe(fmt.Sprintf(":%d", s.port), s.mux)
	if errors.Is(err, http.ErrServerClosed) {
		glog.Info("server closed")
	} else if err != nil {
		glog.Errorf("error starting server: %s", err)
		os.Exit(1)
	}
}
