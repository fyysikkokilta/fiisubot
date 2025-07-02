#!/usr/bin/env python3
"""
Fiisut Telegram Bot - Python Implementation

A Telegram command bot for searching and displaying Finnish student songs from Fiisut-V repository.
Use /fiisu <search_term> to search for songs.
"""

import json
import logging
import os
import html
from typing import List, Dict, Any

from telegram import (
    Update,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode


# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class SongDatabase:
    """Simple in-memory song database with search functionality."""

    def __init__(self, songs_file: str = "songs.json"):
        """Initialize the song database."""
        self.songs: List[Dict[str, Any]] = []
        self.load_songs(songs_file)

    def load_songs(self, songs_file: str) -> None:
        """Load songs from JSON file."""
        try:
            with open(songs_file, "r", encoding="utf-8") as f:
                self.songs = json.load(f)
            logger.info(f"Loaded {len(self.songs)} songs from {songs_file}")
        except FileNotFoundError:
            logger.error(f"Songs file {songs_file} not found")
            self.songs = []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing songs file: {e}")
            self.songs = []

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for songs matching the query.

        This is a simple text-based search that looks for the query
        in song name and lyrics.
        """
        if not query.strip():
            return self.songs[:limit]

        query_lower = query.lower()
        matches = []

        for song in self.songs:
            # Calculate relevance score
            score = 0

            # Higher score for name matches
            if query_lower in song.get("name", "").lower():
                score += 10

            # Lower score for lyrics matches
            if query_lower in song.get("lyrics", "").lower():
                score += 1

            # Add to results if there's a match
            if score > 0:
                matches.append((score, song))

        # Sort by relevance and return top results
        matches.sort(reverse=True, key=lambda x: x[0])
        return [song for _, song in matches[:limit]]


# Global song database instance
song_db = SongDatabase()


def escape_html(text: str) -> str:
    """Remove HTML tags from text."""
    import re

    # Remove HTML tags
    clean_text = re.sub(r"<[^>]+>", "", text)
    return clean_text


def truncate_message(text: str, max_length: int = 4000) -> str:
    """Truncate message if it's too long for Telegram."""
    if len(text) <= max_length:
        return text

    # Find a good place to cut (try to cut at a line break)
    truncated = text[:max_length]
    last_newline = truncated.rfind("\n")

    if last_newline > max_length - 200:  # If we found a newline close to the limit
        truncated = truncated[:last_newline]

    return truncated + "\n\n📝 <i>Viesti katkaistiin pituuden vuoksi...</i>"


async def send_long_message(
    update: Update, text: str, parse_mode=ParseMode.HTML
) -> None:
    """Send a message, splitting it if it's too long."""
    max_length = 4000  # Leave some buffer under Telegram's 4096 limit

    if len(text) <= max_length:
        await update.message.reply_text(
            text, parse_mode=parse_mode, disable_web_page_preview=True
        )
        return

    # Split into chunks
    chunks = []
    remaining = text

    while len(remaining) > max_length:
        # Find a good place to split (prefer line breaks)
        chunk = remaining[:max_length]
        last_newline = chunk.rfind("\n\n")  # Look for paragraph breaks first
        if last_newline == -1:
            last_newline = chunk.rfind("\n")  # Then any line break

        if last_newline > max_length - 200:  # If we found a good break point
            split_point = last_newline
        else:
            split_point = max_length

        chunks.append(remaining[:split_point])
        remaining = remaining[split_point:].lstrip()

    if remaining:
        chunks.append(remaining)

    # Send each chunk
    for i, chunk in enumerate(chunks):
        if i == 0:
            # First chunk - send as reply
            await update.message.reply_text(
                chunk, parse_mode=parse_mode, disable_web_page_preview=True
            )
        else:
            # Subsequent chunks - send as follow-up
            await update.effective_chat.send_message(
                chunk, parse_mode=parse_mode, disable_web_page_preview=True
            )


async def fiisu_command_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /fiisu command."""
    # Get the search query from command arguments
    query = " ".join(context.args) if context.args else ""
    logger.info(f"Received /fiisu command with query: {query}")

    if not query.strip():
        # Check if we're in a private chat to show different help
        chat_type = update.effective_chat.type
        if chat_type == "private":
            help_text = (
                "🎵 Käyttö: /fiisu hakusana\n\n"
                "Esimerkki: /fiisu teemu\n"
                "Voit myös kirjoittaa hakusanan suoraan ilman komentoa!\n\n"
                "Hae Fiisuja nimellä tai sanoilla!"
            )
        else:
            help_text = (
                "🎵 Käyttö: /fiisu hakusana\n\n"
                "Esimerkki: /fiisu teemu\n\n"
                "Hae Fiisuja nimellä tai sanoilla!"
            )

        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.HTML,
        )
        return

    # Search for songs
    matching_songs = song_db.search(query, limit=5)

    if not matching_songs:
        await update.message.reply_text(
            f"🔍 Ei tuloksia haulle: <b>{escape_html(query)}</b>\n\n"
            "Kokeile eri hakusanoja!",
            parse_mode=ParseMode.HTML,
        )
        return

    # Format and send results
    if len(matching_songs) == 1:
        # If only one result, send the full song
        song = matching_songs[0]
        name = song.get("name", "Unknown Song")
        lyrics = song.get("lyrics", "No lyrics available")
        melody = song.get("melody")
        composer = song.get("composer")
        arranger = song.get("arranger")
        notes = song.get("notes")

        # Build the message with metadata
        message_text = f"🎵 <b>{escape_html(name)}</b>\n"

        # Add metadata if available
        metadata_parts = []
        if melody:
            metadata_parts.append(f"🎼 Sävel: {escape_html(melody)}")
        if composer:
            metadata_parts.append(f"✍️ Säveltäjä: {escape_html(composer)}")
        if arranger:
            metadata_parts.append(f"🎹 Sovittaja: {escape_html(arranger)}")

        if metadata_parts:
            message_text += "\n" + "\n".join(metadata_parts) + "\n"

        message_text += f"\n{escape_html(lyrics)}"

        # Add notes if available
        if notes:
            message_text += f"\n\n📝 {notes}"

        await send_long_message(update, message_text)
    else:
        # If multiple results, show a list with first few lines of each
        message_text = f"🎵 <b>Löytyi {len(matching_songs)} laulua haulle:</b> {escape_html(query)}\n\n"

        for i, song in enumerate(matching_songs, 1):
            name = song.get("name", "Unknown Song")
            lyrics = song.get("lyrics", "")
            melody = song.get("melody")
            composer = song.get("composer")

            # Build metadata preview
            metadata_preview = []
            if melody:
                metadata_preview.append(f"sävel: {melody}")
            if composer:
                metadata_preview.append(f"säv: {composer}")

            # Show first line or two of lyrics as preview
            lyrics_preview = lyrics.split("\n")[0] if lyrics else "Ei saatavilla"
            if len(lyrics_preview) > 40:
                lyrics_preview = lyrics_preview[:40] + "..."

            # Escape HTML in name and previews
            escaped_name = escape_html(name)
            escaped_lyrics_preview = escape_html(lyrics_preview)

            message_text += f"{i}. <b>{escaped_name}</b>\n"

            # Add metadata if available
            if metadata_preview:
                escaped_metadata = escape_html(" | ".join(metadata_preview))
                message_text += f"   📄 <i>{escaped_metadata}</i>\n"

            message_text += f"   🎵 <i>{escaped_lyrics_preview}</i>\n\n"

        message_text += "💡 Tarkenna hakua saadaksesi koko laulun!"

        await send_long_message(update, message_text)


async def send_help_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start and /help commands."""
    chat_type = update.effective_chat.type

    if chat_type == "private":
        message_text = (
            "🎵 <b>Tervetuloa Fiisut-bottiin!</b>\n\n"
            "Hae suomalaisia opiskelijalauluja:\n"
            "• Komennolla: /fiisu hakusana\n"
            "• Tai kirjoita vain hakusana suoraan\n\n"
            "<b>Esimerkkejä:</b>\n"
            "• /fiisu teemu\n"
            "• /fiisu juomalaulu\n"
            "• /fiisu polyteknikko\n\n"
            f"📚 Tietokannassa on {len(song_db.songs)} laulua Fiisut-V kokoelmasta.\n\n"
            "🇬🇧 For English instructions, use /english"
        )
    else:
        message_text = (
            "🎵 <b>Fiisut-botti</b>\n\n"
            "Hae suomalaisia opiskelijalauluja komennolla:\n"
            "/fiisu hakusana\n\n"
            "<b>Esimerkkejä:</b>\n"
            "• /fiisu teemu\n"
            "• /fiisu juomalaulu\n"
            "• /fiisu polyteknikko\n\n"
            f"📚 Tietokannassa on {len(song_db.songs)} laulua Fiisut-V kokoelmasta.\n\n"
            "🇬🇧 For English instructions, use /english"
        )

    await update.message.reply_text(
        message_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )


async def send_help_message_english(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /english command for English instructions."""
    chat_type = update.effective_chat.type

    if chat_type == "private":
        message_text = (
            "🎵 <b>Welcome to Fiisut Bot!</b>\n\n"
            "Search for Finnish student songs:\n"
            "• With command: /fiisu search_term\n"
            "• Or just type the search term directly\n\n"
            "<b>Examples:</b>\n"
            "• /fiisu teemu\n"
            "• /fiisu juomalaulu (drinking song)\n"
            "• /fiisu polyteknikko (polytechnic)\n\n"
            f"📚 Database contains {len(song_db.songs)} songs from the Fiisut-V collection.\n\n"
            "🇫🇮 Suomenkieliset ohjeet: /help"
        )
    else:
        message_text = (
            "🎵 <b>Fiisut Bot</b>\n\n"
            "Search for Finnish student songs with command:\n"
            "/fiisu search_term\n\n"
            "<b>Examples:</b>\n"
            "• /fiisu teemu\n"
            "• /fiisu juomalaulu (drinking song)\n"
            "• /fiisu polyteknikko (polytechnic)\n\n"
            f"📚 Database contains {len(song_db.songs)} songs from the Fiisut-V collection.\n\n"
            "🇫🇮 Suomenkieliset ohjeet: /help"
        )

    await update.message.reply_text(
        message_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )


async def handle_private_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle private messages that aren't commands."""
    # For now, treat all private messages as search queries
    query = update.message.text.strip()

    if not query:
        await send_help_message(update, context)
        return

    # Simulate /fiisu command
    context.args = query.split()
    await fiisu_command_handler(update, context)


async def handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")


async def post_init(application: Application):
    """Initialize handlers after application is built."""
    # Commands work in both private chats and groups
    application.add_handler(CommandHandler("start", send_help_message))
    application.add_handler(CommandHandler("help", send_help_message))
    application.add_handler(CommandHandler("english", send_help_message_english))
    application.add_handler(CommandHandler("fiisu", fiisu_command_handler))

    # Private messages (non-commands) are treated as search queries
    application.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & ~filters.COMMAND, handle_private_message
        )
    )

    application.add_error_handler(handle_error)

    logger.info("Post init done.")


def main() -> None:
    """Start the bot."""
    # Get bot token from environment
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
        raise ValueError("Bot token not provided")

    # Create application
    app = Application.builder().token(bot_token).concurrent_updates(False).build()
    app.post_init = post_init

    # Start the bot
    logger.info("Starting Fiisut Telegram Bot...")
    app.run_polling()


if __name__ == "__main__":
    main()
