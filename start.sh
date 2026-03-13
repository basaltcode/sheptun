#!/bin/bash

cd "$(dirname "$0")"

trap 'kill 0' EXIT

(cd backend && uvicorn main:app --reload --port 8000) &
(cd frontend && npm run dev) &

wait
