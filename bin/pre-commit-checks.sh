#!/bin/bash
set -e

cd frontend
# npm run build
cd ..

cd backend
pytest tests/
cd ..

