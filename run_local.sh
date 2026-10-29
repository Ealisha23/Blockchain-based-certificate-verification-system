#!/usr/bin/env bash
# Starts Hardhat node + deploys contract + Flask API (+ React dev server with --frontend).
# Prereqs: MySQL/MariaDB running with the DB from Backend/setup_mysql_dev.sql, Python venv at Backend/.venv.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/Backend"
[ -f .env ] || { echo "Create Backend/.env from Backend/.env.example first"; exit 1; }
set -a; . ./.env; set +a
export HARDHAT_USE_SOLCJS="${HARDHAT_USE_SOLCJS:-0}"

( cd contracts && npx hardhat compile >/dev/null && (npx hardhat node >/tmp/bcv_hardhat.log 2>&1 &) )
for i in $(seq 1 30); do curl -s -X POST -H 'content-type: application/json' \
  --data '{"jsonrpc":"2.0","method":"eth_chainId","id":1}' http://localhost:8545 >/dev/null && break; sleep 1; done
( cd contracts && npx hardhat run scripts/deploy.js --network localhost )

echo "First time? create an admin: (cd Backend && . .venv/bin/activate && python -m app.cli create-admin you@example.com)"
if [ "${1:-}" = "--frontend" ]; then ( cd "$ROOT/frontend" && (BROWSER=none npm start >/tmp/bcv_frontend.log 2>&1 &) ); fi
. .venv/bin/activate
exec python3 -m app.api.v1.app
