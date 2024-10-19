FROM python:3.12.7-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    pkg-config && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /

COPY . .

RUN pip install -U --quiet --no-cache-dir pip setuptools && \
    pip install --quiet --no-cache-dir -r requirements.txt && \
    make setup && \
    find bridges/ -type f -name "requirements.txt" -exec pip install --quiet --no-cache-dir -r {} \;

ENV MODE=production

CMD ["python3", "-u", "grpc_server.py"]
