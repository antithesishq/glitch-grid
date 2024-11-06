# Stage 1: Get Golang image
FROM docker.io/library/golang:1.20-bookworm AS builder
LABEL maintainer="Antithesis <support@antithesis.com>"

# Add source code
RUN mkdir -p /go/src/antithesis/vault
COPY go.sum go.mod *.go /go/src/antithesis/vault/

# Download and install antithesis-go-instrumentor
# Installs into $GOPATH/bin => /go/bin
RUN cd /go/src/antithesis/vault && \
go install github.com/antithesishq/antithesis-sdk-go/tools/antithesis-go-instrumentor@46403e51151e5ac9078678d18f26673013c748af && \
go mod tidy

# Create the destination output directory for the instrumented code.
RUN mkdir -p /go/src/antithesis/vault-instrumented

# Perform instrumentation
RUN /go/bin/antithesis-go-instrumentor \
/go/src/antithesis/vault \
/go/src/antithesis/vault-instrumented

# Build vault binary
RUN cd /go/src/antithesis/vault-instrumented/customer && \
go build -o vault *.go

# Stage 2: lightweight "release"
FROM docker.io/library/debian:bookworm-slim
LABEL maintainer="Antithesis <support@antithesis.com>"

# Copy the instrumented binary, and symbols from the build image.
COPY --from=builder \
/go/src/antithesis/vault-instrumented/customer/vault /bin/
RUN mkdir -p /symbols
COPY --from=builder /go/src/antithesis/vault-instrumented/symbols /symbols/

ENTRYPOINT [ "/bin/vault" ]
