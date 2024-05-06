FROM python:3.12-slim

LABEL org.opencontainers.image.source=https://github.com/pythonistaguild/mystbin-backend
LABEL org.opencontainers.image.description="Mystbin's Python Backend"
LABEL org.opencontainers.image.licenses=GPLv3

RUN mkdir -p /etc/apt/keyrings \
    && apt update -y \
    && apt-get install --no-install-recommends -y \
    # deps for building python deps
    git \
    build-essential \
    libcurl4-gnutls-dev \
    gnutls-dev \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/*

# copy project requirement files here to ensure they will be cached.
WORKDIR /app
COPY requirements.txt ./

# install runtime deps
RUN pip install -Ur requirements.txt

COPY . /app/
ENTRYPOINT python -O launcher.py
