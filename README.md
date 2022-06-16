# Fiisut telegram bot

Telegram inline bot written in Rust using `milli` as its full-text search engine.

Songs are extracted from Fiisut-V latex files with a hacky script at `tools/extract_songs.py` to a `documents.json` file which is read a Rust indexer binary that creates the indexes the bot binary actually uses.

