#!/bin/bash
# robust start script for backend

# Default to 8000 if PORT is not set
PORT="${PORT:-8000}"

echo "Starting Backend on PORT=$PORT"
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
