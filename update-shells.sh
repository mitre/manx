#!/bin/bash
GOOS=windows go build -o payloads/manx.go-windows -ldflags="-s -w" shells/manx.go
GOOS=linux go build -o payloads/manx.go-linux -ldflags="-s -w" shells/manx.go
GOOS=darwin go build -o payloads/manx.go-darwin -ldflags="-s -w" shells/manx.go
