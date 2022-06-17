FROM docker.io/python:alpine AS extractor
RUN pip install TexSoup tqdm
WORKDIR /data
COPY tools/extract_songs.py /data/
COPY Fiisut-V/ /data/Fiisut-V/
RUN python extract_songs.py

FROM docker.io/rust:alpine AS builder
RUN apk add --no-cache musl-dev
WORKDIR /data
COPY Cargo.toml Cargo.lock /data
RUN cargo fetch
RUN mkdir -p src/indexer && touch src/main.rs src/indexer/main.rs \
  && cargo build --release --offline --target=x86_64-unknown-linux-musl; exit 0
RUN rm -rf src/
COPY src/ /data/src/
RUN cargo build --release --offline --target=x86_64-unknown-linux-musl --bins
COPY --from=extractor /data/songs.json /data/songs.json
RUN target/x86_64-unknown-linux-musl/release/index-builder

FROM docker.io/alpine
ENV TELOXIDE_TOKEN=
WORKDIR /data
COPY songs.json /data/songs.json
COPY --from=builder  /data/target/x86_64-unknown-linux-musl/release/fiisut_tg /data/data.mdb /data/lock.mdb /data/
RUN ls /data
#RUN exit 1
ENTRYPOINT ["/data/fiisut_tg"]
CMD [""]
