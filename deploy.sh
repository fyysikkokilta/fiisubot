#!/bin/bash
python tools/extract_songs.py
cargo run --bin index-builder

# TODO: Statick link
cargo build --bin fiisut_tg --release
TELOXIDE_TOKEN=$TELOXIDE_TOKEN

scp -pr target/release/fiisut_tg data.mdb kosh.aalto.fi:~/fiisut-tg
ssh kosh.aalto.fi "cd fiisut-tg && TELOXIDE_TOKEN=$TELOXIDE_TOKEN screen -dmS myscreen ./fiisut_tg"

