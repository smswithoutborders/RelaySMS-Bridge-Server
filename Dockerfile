FROM python:3.13.1-slim

WORKDIR /bridge_server

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    pkg-config && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


COPY requirements.txt .

RUN pip install --disable-pip-version-check --quiet --no-cache-dir setuptools && \
    pip install --disable-pip-version-check --quiet --no-cache-dir -r requirements.txt

COPY . .

RUN make setup && \
    find bridges/ -type f -name "requirements.txt" -exec pip install --quiet --no-cache-dir -r {} \;

ENV MODE=production

CMD ["python3", "-u", "grpc_server.py"]
