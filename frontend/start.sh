#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

# Install dependencies if node_modules missing or outdated
if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules" ]; then
  echo "Installing dependencies..."
  npm install
fi

# Create .env if missing
if [ ! -f ".env" ]; then
  echo "VITE_API_URL=http://localhost:8000" > .env
  echo "Created .env with default API URL."
fi

echo "Starting frontend on http://localhost:5173"
npm run dev
