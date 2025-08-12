FROM python:3.13.6-slim

WORKDIR /bridge_server

RUN --mount=type=cache,sharing=locked,target=/var/cache/apt \
    --mount=type=cache,sharing=locked,target=/var/lib/apt \
    apt-get update && apt-get install -y --no-install-recommends \    
    build-essential \
    git \
    vim \
    curl \
    supervisor \
    pkg-config && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


COPY requirements.txt .

RUN --mount=type=cache,sharing=locked,target=/root/.cache/pip \
    pip install --disable-pip-version-check --quiet --no-cache-dir -r requirements.txt

COPY . .
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN --mount=type=cache,sharing=locked,target=/root/.cache/pip \
    make setup && \
    find bridges/ -type f -name "requirements.txt" -exec \
    pip install --disable-pip-version-check --quiet --no-cache-dir -r {} \;

ENV MODE=production

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
