FROM rust:1.92.0-slim-trixie@sha256:bf3368a992915f128293ac76917ab6e561e4dda883273c8f5c9f6f8ea37a378e AS build
WORKDIR /build
COPY Cargo.toml Cargo.lock ./
COPY src ./src
COPY contracts ./contracts
RUN --mount=type=cache,target=/usr/local/cargo/registry --mount=type=cache,target=/build/target cargo build --locked --release && cp target/release/soil-data-access /soil-data-access

FROM debian:trixie-slim@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2
COPY --from=build /soil-data-access /usr/local/bin/soil-data-access
USER 10001:10001
ENV LISTEN_ADDR=0.0.0.0:8080
ENTRYPOINT ["/usr/local/bin/soil-data-access"]
