FROM golang:1.27-alpine AS build

WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o /pingarchive-engine

RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags="-s -w" \
    -o /out/pingarchive-engine .

FROM alpine:3.22

RUN apk add --no-cache ca-certificates
COPY --from=build /out/pingarchive-engine /usr/local/bin/pingarchive-engine

ENTRYPOINT ["pingarchive-engine"]
# ENTRYPOINT ["/bin/sh", "-c", "while true; do sleep 3600; done"]
