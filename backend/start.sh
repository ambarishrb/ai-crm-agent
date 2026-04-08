#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Copy .env from example if missing
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env from .env.example — update it with your credentials."
fi

# Start PostgreSQL if docker is available
if command -v docker &> /dev/null; then
  if ! docker ps --format '{{.Names}}' | grep -q hcp_postgres; then
    echo "Starting PostgreSQL..."
    docker-compose up -d
    sleep 2
  else
    echo "PostgreSQL already running."
  fi
else
  echo "Warning: Docker not found. Make sure PostgreSQL is running on port 5432."
fi

# Run migrations if alembic is configured
if [ -f "alembic.ini" ]; then
  echo "Running migrations..."
  alembic upgrade head
fi

# Seed data
echo "Seeding database..."
python -m app.seed || true

# Start server
echo "Starting backend on http://localhost:8000"
uvicorn app.main:app --reload --port 8000
