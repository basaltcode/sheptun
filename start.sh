#!/bin/bash
# Browser-mode (no Tauri): run the Python backend + Vite dev server.
# For the native desktop app in dev mode, use `npm run dev` instead.

cd "$(dirname "$0")"

trap 'kill 0' EXIT

(cd backend && ./venv/bin/uvicorn main:app --reload --port 8000) &
(cd frontend && npm run dev) &

wait
