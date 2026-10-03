#!/bin/bash
set -e

git checkout main
git pull
last_tag=$(git tag | sort -V | tail -1)
echo "Checking out $last_tag"
git checkout $last_tag

mkdir ./pip-wheel-house
pip download -r requirements.txt -d ./pip-wheel-house
pip install --no-index --find-links=./pip-wheelhouse -r requirements.txt

echo "Building containers"
cd container
export APP_VERSION=$last_tag
docker compose down
docker system prune -f --all
docker compose build --no-cache
docker compose up -d


