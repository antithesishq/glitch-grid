# Stage 1: Get Golang image
FROM docker.io/library/golang:1.20-bookworm AS builder
LABEL maintainer="Antithesis <support@antithesis.com>"

# Add source code
RUN mkdir -p /go/src/antithesis/control
COPY go.sum go.mod *.go /go/src/antithesis/control/

# Download and install antithesis-go-instrumentor
# Installs into $GOPATH/bin => /go/bin
RUN cd /go/src/antithesis/control && \
go install github.com/antithesishq/antithesis-sdk-go/tools/antithesis-go-instrumentor@v0.3.6 && \
go mod tidy

# Create the destination output directory for the instrumented code.
RUN mkdir -p /go/src/antithesis/control-instrumented

# Perform instrumentation
RUN /go/bin/antithesis-go-instrumentor \
/go/src/antithesis/control \
/go/src/antithesis/control-instrumented
    
# Build control binary
RUN cd /go/src/antithesis/control-instrumented/customer && \
cat *_antithesis_catalog.go && \
go build -o control *.go

# Stage 2: lightweight "release"
FROM docker.io/library/debian:bookworm-slim
LABEL maintainer="Antithesis <support@antithesis.com>"

# Copy the instrumented binary, and symbols from the build image.
COPY --from=builder \
/go/src/antithesis/control-instrumented/customer/control /bin/
RUN mkdir -p /symbols
COPY --from=builder /go/src/antithesis/control-instrumented/symbols /symbols/

ENTRYPOINT [ "/bin/control" ]
