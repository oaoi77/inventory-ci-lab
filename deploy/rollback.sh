#!/bin/sh
# Manual rollback: switch nginx traffic back to the other colour.
# Run from the project folder:  sh deploy/rollback.sh
set -eu
PROXY=inventory-proxy
if docker exec "$PROXY" grep -q inventory-green /etc/nginx/conf.d/default.conf; then
  TARGET=blue
else
  TARGET=green
fi
echo "Checking inventory-$TARGET before switching..."
docker exec "$PROXY" wget -qO- "http://inventory-$TARGET:5000/health"
echo
docker cp "deploy/nginx-$TARGET.conf" "$PROXY:/etc/nginx/conf.d/default.conf"
docker exec "$PROXY" nginx -t
docker exec "$PROXY" nginx -s reload
echo "Traffic switched back to $TARGET"
