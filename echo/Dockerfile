FROM rust:latest AS build

ARG PROFILE=release

WORKDIR /build

RUN mkdir bin && \
    apt update -y && apt upgrade -y && apt install -y musl-tools && \
    rustup target add x86_64-unknown-linux-musl

# Mounting src using bind mount is slower for some reason
COPY src src
ENV RUSTFLAGS='-C target-feature=+crt-static'

# NOTE: Due to caching this is actually faster than using
# Two separate cargo builds (one without source present).
RUN --mount=type=cache,target=target \
    --mount=type=cache,target=/usr/local/cargo/git \
    --mount=type=cache,target=/usr/local/cargo/registry \
    --mount=type=bind,source=Cargo.toml,target=Cargo.toml,readwrite \
    --mount=type=bind,source=Cargo.lock,target=Cargo.lock,readwrite \
    # Use musl target as the binary is about 1MiB smaller
    cargo build --profile $PROFILE --target x86_64-unknown-linux-musl && \
    # The "dev" target directory is named "debug" instead
    [ $PROFILE = "dev" ] && FOLDER="debug" || FOLDER="release"; \
    # Copy output into an unmounted directory for copying
    cp target/x86_64-unknown-linux-musl/$FOLDER/echo /build/bin && \
    cp target/x86_64-unknown-linux-musl/$FOLDER/healthcheck /build/bin

FROM scratch AS image

ARG PROFILE

LABEL org.opencontainers.image.title="MystBin Echo"
LABEL org.opencontainers.image.authors="Lilly Rose Berner <lilly@lostluma.net>"

EXPOSE 8000
WORKDIR /opt/echo

# Non-empty value to enable
ENV RUST_BACKTRACE=$PROFILE

ENV PATH=/opt/echo/bin
ENV ROCKET_CONFIG=/etc/opt/echo/Rocket.toml

COPY Rocket.toml $ROCKET_CONFIG

COPY --from=build /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Copy last so prior steps are cached doing many rebuilds
COPY --from=build /build/bin bin

HEALTHCHECK --interval=5s --timeout=5s --retries=1 CMD ["healthcheck"]

USER 101:101
CMD ["echo"]
