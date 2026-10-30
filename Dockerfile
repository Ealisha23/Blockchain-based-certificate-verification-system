FROM node:20-slim AS contract
WORKDIR /c
COPY Backend/contracts/ .
RUN npm install && npx hardhat compile

FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config default-libmysqlclient-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY Backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY Backend/ .
COPY --from=contract /c/artifacts ./contracts/artifacts
CMD exec gunicorn -b 0.0.0.0:${PORT:-10000} -w 2 --threads 4 app.api.v1.app:app