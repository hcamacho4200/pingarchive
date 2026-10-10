#!/bin/bash
export APP_VERSION=$(git tag | sort -V | tail -1)
echo "Building containers with version $APP_VERSION"

cd pingarchive-ping-engine
docker build \
    -t pingarchive-engine:$APP_VERSION \
    -t pingarchive-ping-engine:testing \
    .
cd ..

cd backend
docker build \
    -t pingarchive-backend:$APP_VERSION \
    -t pingarchive-backend:testing \
    .
cd ..

cd frontend
docker build \
    -t pingarchive-frontend:$APP_VERSION \
    -t pingarchive-frontend:$testing \
    .
cd ..

echo "Containers built with version $APP_VERSION and tagged for testing"