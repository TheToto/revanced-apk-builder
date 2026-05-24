#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="flaresolverr"
PORT=8191

if ! command -v docker &>/dev/null; then
	echo "[-] Error: docker is not installed. Please install Docker to run FlareSolverr." >&2
	exit 1
fi

if docker ps -a --format '{{.Names}}' | grep -Eq "^${CONTAINER_NAME}$"; then
	if docker ps --format '{{.Names}}' | grep -Eq "^${CONTAINER_NAME}$"; then
		echo "[+] FlareSolverr is already running."
	else
		echo "[+] Starting existing FlareSolverr container..."
		docker start "$CONTAINER_NAME"
	fi
else
	echo "[+] Starting new FlareSolverr container..."
	docker run -d \
		--name "$CONTAINER_NAME" \
		-p ${PORT}:${PORT} \
		-e LOG_LEVEL=info \
		-e CAPTCHA_SOLVER=none \
		flaresolverr/flaresolverr:latest
fi

echo "[+] Waiting for FlareSolverr to be ready..."
timeout 30 sh -c "until curl -s http://localhost:${PORT}/ > /dev/null; do sleep 1; done"

echo "[+] FlareSolverr is ready at http://localhost:${PORT}/v1"
echo "[+] To run build.sh with FlareSolverr, run:"
echo "    export FLARESOLVERR_URL=http://localhost:${PORT}/v1"
echo "    ./build.sh"
