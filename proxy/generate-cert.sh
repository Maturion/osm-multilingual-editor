#!/usr/bin/env bash
# Generates a self-signed HTTPS cert for local dev (https://localhost).
# Not committed to git (proxy/certs/ is gitignored) - run this once per checkout.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/certs"
mkdir -p "$DIR"

openssl req -x509 -nodes -newkey rsa:2048 \
  -keyout "$DIR/localhost-key.pem" \
  -out "$DIR/localhost.pem" \
  -days 397 \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1,IP:::1"

echo "Generated $DIR/localhost.pem and $DIR/localhost-key.pem"
