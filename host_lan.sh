#!/usr/bin/env sh
set -eu

PORT="${PORT:-8000}"

cd "$(dirname "$0")"

LAN_IP=""

if command -v hostname >/dev/null 2>&1; then
    LAN_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
fi

if [ -z "${LAN_IP}" ] && command -v ip >/dev/null 2>&1; then
    LAN_IP="$(ip route get 1 2>/dev/null | awk '/src/ {for (i = 1; i <= NF; i++) if ($i == "src") {print $(i + 1); exit}}')"
fi

echo "Hosting QuizUrself on your local network..."
echo
if [ -n "${LAN_IP}" ]; then
    echo "Open this on other devices on the same LAN:"
    echo "  http://${LAN_IP}:${PORT}"
else
    echo "Could not auto-detect your LAN IP."
    echo "Open this on other devices on the same LAN:"
    echo "  http://YOUR-LAN-IP:${PORT}"
    echo
    echo "To find your LAN IP on Linux, try one of:"
    echo "  hostname -I"
    echo "  ip addr"
fi
echo
echo "Press Ctrl+C to stop the server."
echo

python3 -m http.server "${PORT}" --bind 0.0.0.0
