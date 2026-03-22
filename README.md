# qBittorrent Cleaner

A Python script to automatically clean up your qBittorrent seeding list based on configurable criteria.

## Features

- Connects to qBittorrent Web UI API
- Smart cleanup logic:
  - Protects young torrents (under 14 days)
  - Removes least popular torrents first (based on qBittorrent's popularity metric)
  - Maintains minimum seeding count (for private tracker requirements)
- Dry-run mode to preview changes
- Configurable via environment variables
- Comprehensive logging

## Installation

1. Install [uv](https://github.com/astral-sh/uv) (fast Python package installer)
2. Clone this repository
3. Copy `.env.example` to `.env` and edit with your settings
4. Install dependencies:

```bash
uv sync
```

## Configuration

Copy `.env.example` to `.env` and edit the values:

```bash
# qBittorrent connection
QBIT_URL=https://your-qbittorrent-host:8080
QBIT_USERNAME=your-username
QBIT_PASSWORD=your-password
# QBIT_VERIFY_SSL=false          # auto-detected from URL if omitted

# Cleanup criteria
QBIT_MINIMUM_SEEDING_TORRENTS=15  # minimum private torrents to keep
QBIT_MINIMUM_SEEDING_TIME_DAYS=14 # days before a torrent can be removed

# Logging
QBIT_LOG_LEVEL=INFO               # DEBUG, INFO, WARNING, ERROR
# QBIT_LOG_FILE=qbitcleaner.log   # omit to log to stdout only
```

All variables are prefixed with `QBIT_` and have sensible defaults.

## Usage

### Basic usage

```bash
uv run qbitcleaner.py
```

### Dry run (preview changes without removing)

```bash
uv run qbitcleaner.py --dry-run
```

### Scheduled Execution

Run the script on a cron schedule:

```bash
uv run qbitcleaner.py --schedule "0 */6 * * *"  # every 6 hours
uv run qbitcleaner.py --schedule "0 0 * * *"    # daily at midnight
uv run qbitcleaner.py --schedule "0 0 * * 0"    # weekly on Sunday
uv run qbitcleaner.py --schedule "0 3 * * *"    # daily at 3 AM
```

Or set the `QBIT_SCHEDULE` environment variable:

```bash
export QBIT_SCHEDULE="0 0 * * *"
uv run qbitcleaner.py
```

## Docker Support

The easiest way to run the cleaner on a schedule is using Docker Compose.

Create a `docker-compose.yml`:

```yaml
version: '3.8'
services:
  qbitcleaner:
    # Build from local source or use ghcr.io image
    build: .
    # image: ghcr.io/martin09/qbitcleaner:latest
    container_name: qbitcleaner
    restart: unless-stopped
    environment:
      - QBIT_URL=http://qbittorrent:8080
      - QBIT_USERNAME=admin
      - QBIT_PASSWORD=adminadmin
      - QBIT_SCHEDULE=0 0 * * *  # daily at midnight
    # Alternative: load from .env file
    # env_file: .env
```

## How It Works

The script:
1. Connects to your qBittorrent instance
2. Fetches all seeding torrents
3. Protects young torrents (under `QBIT_MINIMUM_SEEDING_TIME_DAYS`)
4. Sorts remaining torrents by popularity (lowest first)
5. Removes least popular torrents until `QBIT_MINIMUM_SEEDING_TORRENTS` remain
6. Logs all actions for review

## Cleanup Logic

**Protected torrents:**
- Seeding for less than `QBIT_MINIMUM_SEEDING_TIME_DAYS` (default: 14 days)

**Removal order:**
- Torrents are sorted by qBittorrent's popularity metric (ratio / time active in months)
- Least popular torrents are removed first
- Removal stops when `QBIT_MINIMUM_SEEDING_TORRENTS` threshold is reached

## Development

### Setup

```bash
uv sync --extra dev
uv run pre-commit install
```

### Run tests

```bash
uv run pytest
```

### Run linting

```bash
uv run ruff check --fix .
uv run ruff format .
```

## Notes

- The script only removes torrents from qBittorrent, not the actual files
- Make sure qBittorrent Web UI is enabled and accessible
- **Always test with `--dry-run` first** to see what would be removed
- Keep your `.env` file private since it contains your credentials
