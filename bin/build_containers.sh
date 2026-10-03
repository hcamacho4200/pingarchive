#!/bin/bash
export APP_VERSION=$(git tag | sort -V | tail -1)
echo "Building containers with version $APP_VERSION"

docker compose down
docker system prune -f --all
docker compose build --no-cache
docker compose up -d

