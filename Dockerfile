# Multi-stage build for Python Fiisut Telegram Bot
ARG PY_VER=3.13

# Stage 1: Extract songs from LaTeX files
FROM python:${PY_VER}-slim AS extractor

# Install dependencies for song extraction
RUN pip install --no-cache-dir TexSoup tqdm

# Set working directory
WORKDIR /app

# Copy extraction tools and song data
COPY extract_songs.py ./
COPY Fiisut-V/ ./Fiisut-V/

# Extract songs to JSON
RUN python extract_songs.py

# Stage 2: Production image
FROM python:${PY_VER}-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TELEGRAM_BOT_TOKEN=""

# Install runtime dependencies
RUN pip install --no-cache-dir python-telegram-bot

# Set working directory
WORKDIR /app

# Copy the bot code
COPY fiisubot.py ./

# Copy the extracted songs from the previous stage
COPY --from=extractor /app/songs.json ./songs.json

# Run the bot
CMD ["python", "fiisubot.py"]
