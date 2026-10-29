FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config default-libmysqlclient-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY Backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY Backend/ .
# Cloud Run provides $PORT
CMD exec gunicorn -b :$PORT -w 2 --threads 4 app.api.v1.app:app
