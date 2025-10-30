ARG PYTHON_BASE=3.13-slim-bookworm
ARG UV_BASE=python3.13-bookworm-slim

FROM ghcr.io/astral-sh/uv:${UV_BASE} AS builder

ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /project

# install latest git
RUN apt-get update -y \
    && apt-get upgrade -y \
    && apt-get install --no-install-recommends --no-install-suggests -y git \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=/project/pyproject.toml \
    --mount=type=bind,source=uv.lock,target=/project/uv.lock \
    uv sync --frozen --no-install-project --no-dev

ADD --chown=1000:1000 . /project

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

FROM python:${PYTHON_BASE}

LABEL org.opencontainers.image.source=https://github.com/pythonistaguild/mystbin
LABEL org.opencontainers.image.description="A paste service built for simplicity and beauty"

USER 1000:1000

WORKDIR /app

COPY --from=builder --chown=1000:1000 /project /app
ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "-O", "launcher.py"]
