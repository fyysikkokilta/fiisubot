# Fiisut Telegram Bot

A Telegram command bot for searching and displaying Finnish student songs from the [Fiisut-V](https://github.com/fyysikkokilta/Fiisut-V) repository.

## Features

- **Command Search**: Use `/fiisu <search_query>` to search for songs
- **Song Display**: Returns formatted song lyrics with HTML formatting
- **Fast Search**: Simple but effective text-based search through song names and lyrics
- **Smart Results**: Shows single song directly or list of matches for broader searches

## Quick Start with Docker Compose

The easiest way to run the bot is using Docker Compose:

1. **Clone and setup**:

   ```bash
   git clone <your-repo-url>
   cd fiisubot
   git submodule init && git submodule update
   ```

2. **Configure environment**:

   ```bash
   cp .env.example .env
   # Edit .env and add your TELEGRAM_BOT_TOKEN
   ```

3. **Run the bot**:

   ```bash
   docker-compose up -d
   ```

4. **View logs**:
   ```bash
   docker-compose logs -f bot
   ```

## Development Setup

### Local Development

1. **Clone the repository**:

   ```bash
   git clone <your-repo-url>
   cd fiisubot
   ```

2. **Initialize the Fiisut-V submodule**:

   ```bash
   git submodule init
   git submodule update
   ```

3. **Install dependencies**:

   ```bash
   pip install python-telegram-bot
   ```

   Or using Poetry:

   ```bash
   poetry install
   ```

4. **Extract songs**:

   ```bash
   python extract_songs.py
   ```

5. **Create bot and get token**:

   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Create a new bot with `/newbot`
   - Copy the bot token

6. **Set environment variable**:

   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   ```

7. **Run the bot**:
   ```bash
   python fiisubot.py
   ```

### Docker Development

For development with live code reloading:

```bash
# Copy environment file
cp .env.example .env
# Add your bot token to .env

# Run in development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## Production Deployment

### Docker Compose (Recommended)

```bash
# Production deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Update deployment
docker-compose pull
docker-compose up -d
```

### Manual Docker

```bash
# Build the image
docker build -t fiisubot .

# Run the container
docker run -d \
  --name fiisubot \
  --restart unless-stopped \
  -e TELEGRAM_BOT_TOKEN="your_bot_token_here" \
  fiisubot
```

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment:

### Workflows

- **CI/CD Pipeline** (`.github/workflows/ci.yml`):

  - **Linting**: Code formatting with Black and linting with Pylint
  - **Testing**: Unit tests and bot functionality validation
  - **Build**: Multi-platform Docker image build and push to GHCR

### Docker Images

Production images are automatically built and pushed to GitHub Container Registry:

```bash
# Latest (main branch)
docker pull ghcr.io/fyysikkokilta/fiisubot:latest

# Specific version
docker pull ghcr.io/fyysikkokilta/fiisubot:v1.0.0
```

### Development Tools

```bash
# Run tests
poetry run test

# Format code
poetry run format

# Check formatting
poetry run format-check

# Lint code
poetry run lint

# Extract songs
poetry run extract-fiisut
```

### Creating a Release

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` (if exists)
3. Create and push a version tag:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
4. GitHub Actions will automatically create a release and build images

## Configuration

### Environment Variables

| Variable             | Description                                 | Default      |
| -------------------- | ------------------------------------------- | ------------ |
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather                   | **Required** |
| `LOG_LEVEL`          | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO`       |
| `PYTHONUNBUFFERED`   | Python output buffering                     | `1`          |

### Docker Compose Files

- `docker-compose.yml` - Base configuration
- `docker-compose.prod.yml` - Production overrides (uses GHCR images)

## Usage

Once the bot is running:

1. Start a chat with your bot
2. Use `/start` to see the welcome message and instructions
3. Use `/fiisu <search_term>` to search for songs
4. The bot will send the formatted song lyrics

Examples:

- `/fiisu teemu` - Search for songs containing "teemu"
- `/fiisu juomalaulu` - Search for drinking songs
- `/fiisu polyteknikko` - Search for polytechnic songs

## Management Commands

### Docker Compose

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart service
docker-compose restart bot

# View logs
docker-compose logs -f bot

# Update and restart
docker-compose pull && docker-compose up -d

# Check resource usage
docker stats fiisubot
```

### Poetry Tasks

```bash
# Extract songs
poetry run extract-fiisut

# Run bot
poetry run bot

# Run tests
poetry run test

# Format code
poetry run format

# Lint code
poetry run lint
```

## Project Structure

```
fiisubot/
├── fiisubot.py                 # 🤖 Main bot file
├── extract_songs.py            # 🎵 Song extraction script
├── songs.json                  # 📄 Song database (generated)
├── Fiisut-V/                   # 📁 Song repository (submodule)
├── .github/                    # 🔄 CI/CD workflows
│   ├── workflows/
│       └── ci-cd.yml           # Main CI/CD pipeline
├── docker-compose.yml          # 🐳 Base Docker Compose config
├── docker-compose.prod.yml     # 🚀 Production overrides
├── Dockerfile                  # 📦 Container definition
├── .env.example                # ⚙️ Environment template
├── pyproject.toml              # 📋 Python dependencies
└── README.md                   # 📖 This file
```

## Monitoring

### Health Checks

The bot includes health checks that verify connectivity to Telegram's API:

```bash
# Check health status
docker-compose exec bot python -c "import requests; print('✓ Healthy' if requests.get('https://api.telegram.org').status_code == 200 else '✗ Unhealthy')"
```

### Logs

View real-time logs:

```bash
# All logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100 bot

# Error logs only
docker-compose logs -f bot | grep ERROR
```

## Troubleshooting

### Common Issues

1. **Bot not responding**: Check if the token is correct and the bot is started
2. **No songs found**: Ensure `songs.json` exists and contains data
3. **Permission denied**: Check if inline mode is enabled for your bot

### Debug Mode

Run with debug logging:

```bash
# Local
LOG_LEVEL=DEBUG python fiisubot.py

# Docker Compose
echo "LOG_LEVEL=DEBUG" >> .env
docker-compose restart bot
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `poetry run test`
5. Format code: `poetry run format`
6. Create a pull request

The CI pipeline will automatically run tests and linting on your PR.

## Dependencies

- `python-telegram-bot` - Telegram Bot API wrapper
- `tqdm` - Progress bars for extraction
- `TexSoup` - LaTeX parsing (for extraction)

## License

MIT for code, all copyrights held for songs from Fiisut-V.
