# Deployment guide (no GitHub needed)

Architecture: React static files + Flask API (gunicorn) + MySQL + smart contract on an Ethereum network.
The backend wallet (`BCV_PRIVATE_KEY`) owns the contract and signs every transaction, so users do not need MetaMask.

## 1. Put the contract on a public testnet (once)
1. Get a free RPC URL (Alchemy / Infura) for **Sepolia**.
2. Create a NEW wallet just for this app; fund it with free Sepolia ETH from a faucet. Never reuse a wallet that holds real money.
3. Deploy:
   ```bash
   cd Backend/contracts && npm install
   DEPLOY_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/KEY \
   DEPLOY_PRIVATE_KEY=0xYOURKEY \
   npx hardhat run scripts/deploy.js --network remote
   ```
4. Note the printed contract address.

## 2. Backend + database on a Linux VPS (Ubuntu 22.04/24.04)
Any VPS works (DigitalOcean, Hetzner, AWS Lightsail...).

From your computer, upload the project zip (no git):
```bash
scp block_aaryan_fixed.zip user@SERVER_IP:/tmp/
```
On the server:
```bash
sudo apt update && sudo apt install -y python3-venv build-essential pkg-config libmysqlclient-dev mysql-server nginx unzip
sudo useradd -r -m bcv
sudo mkdir -p /opt/bcv && sudo unzip /tmp/block_aaryan_fixed.zip -d /tmp/bcv_src
sudo cp -r /tmp/bcv_src/*/* /opt/bcv/ && sudo chown -R bcv:bcv /opt/bcv

# database
sudo mysql -e "CREATE DATABASE bcv CHARACTER SET utf8mb4; CREATE USER 'bcv'@'localhost' IDENTIFIED BY 'STRONG_PASSWORD'; GRANT ALL ON bcv.* TO 'bcv'@'localhost';"

# backend
sudo -u bcv bash -c 'cd /opt/bcv/Backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && cp .env.example .env'
```
Edit `/opt/bcv/Backend/.env`:
```
BCV_MYSQL_USER=bcv
BCV_MYSQL_PWD=STRONG_PASSWORD
BCV_MYSQL_DB=bcv
BCV_ENV=prod
BCV_DEV=0
SECRET_KEY=<python3 -c "import secrets;print(secrets.token_hex(32))">
BCV_CORS_ORIGINS=https://example.com
BCV_WEB3_PROVIDER=https://eth-sepolia.g.alchemy.com/v2/KEY
BCV_CONTRACT_ADDRESS=<address from step 1>
BCV_PRIVATE_KEY=<the deployer wallet key>
```
Contract ABI file is required by the API, so compile once on the server:
```bash
cd /opt/bcv/Backend/contracts && sudo -u bcv npm install && sudo -u bcv npx hardhat compile
```
Create your first admin, then start the service:
```bash
cd /opt/bcv/Backend && sudo -u bcv bash -c 'set -a; . ./.env; set +a; .venv/bin/python -m app.cli create-admin you@example.com "Your Name"'
sudo cp /opt/bcv/deploy/bcv-api.service /etc/systemd/system/
sudo systemctl enable --now bcv-api
curl http://127.0.0.1:5000/api/v1/status      # {"status":"OK"}
```
`chmod 600 /opt/bcv/Backend/.env` — it holds your wallet key.

## 3. Frontend
On your computer:
```bash
cd frontend
cp .env.example .env     # set REACT_APP_API_URL=https://example.com/api/v1 (+ Firebase keys if used)
npm install --legacy-peer-deps
npm run build
```
Upload `frontend/build/` to the server: `scp -r build/* user@SERVER_IP:/var/www/bcv/`
Then use `deploy/nginx.conf` (serves the site and proxies `/api/` to the backend):
```bash
sudo cp /opt/bcv/deploy/nginx.conf /etc/nginx/sites-available/bcv   # edit server_name
sudo ln -s /etc/nginx/sites-available/bcv /etc/nginx/sites-enabled/ && sudo nginx -t && sudo systemctl reload nginx
```

## 4. HTTPS (required for login tokens)
Point your domain's A record at the server, then:
```bash
sudo apt install -y certbot python3-certbot-nginx && sudo certbot --nginx -d example.com
```

## Alternative: frontend on a free static host without Git
Netlify "Drop" (app.netlify.com/drop) or Cloudflare Pages direct upload accept the `build/` folder by drag-and-drop (`public/_redirects` is already included for routing). Then set `BCV_CORS_ORIGINS` on the backend to that site's URL and build the frontend with `REACT_APP_API_URL` pointing at your HTTPS backend.

## Local run (for testing)
See README "Quick local setup". First admin locally: `cd Backend && python -m app.cli create-admin you@example.com`.

## Notes
- Firebase (PDF/image upload) needs its own free project; set Storage rules to require auth in production.
- Back up the MySQL database; blockchain data alone cannot recreate accounts.

## Option: Firebase Hosting + Google Cloud Run
Files already included: `Dockerfile` and `.dockerignore` (project root), `frontend/firebase.json` and `frontend/.firebaserc` (replace `PROJECT_ID`; change `asia-south1` in both firebase.json and the gcloud commands if you use another region).
Steps: compile the contract (`cd Backend/contracts && npm install && npx hardhat compile`), then run `gcloud run deploy bcv-api --source .` from the project root, then `npm run build && firebase deploy --only hosting` from `frontend/` with `REACT_APP_API_URL=/api/v1` in `frontend/.env`.
