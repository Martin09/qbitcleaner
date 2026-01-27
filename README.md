# qBittorrent Cleaner

A Python script to automatically clean up your qBittorrent seeding list based on configurable criteria.

## Features

- Connects to qBittorrent Web UI API
- Smart cleanup logic:
  - Protects young torrents (under 14 days)
  - Removes least popular torrents first (based on qBittorrent's popularity metric)
  - Maintains minimum seeding count (for private tracker requirements)
- Dry-run mode to preview changes
- Configurable via YAML file
- Comprehensive logging

## Installation

1. Install [uv](https://github.com/astral-sh/uv) (fast Python package installer)
2. Clone this repository
3. Copy `config.example.yaml` to `config.yaml` and edit with your settings
4. Install dependencies:

```bash
uv sync
```

## Configuration

Copy `config.example.yaml` to `config.yaml` and edit:

- **qbittorrent**: Connection settings
  - `url`: Full URL including protocol, hostname, port, and optional path
  - `username` / `password`: Your qBittorrent credentials
  - `verify_ssl`: Set to `false` for self-signed certificates
- **cleanup**: Criteria for removing torrents
  - `minimum_seeding_torrents`: Minimum torrents to keep seeding (default: 15)
  - `minimum_seeding_time_days`: Days before a torrent can be removed (default: 14)
- **logging**: Log level and file path

## Usage

### Basic usage

```bash
uv run qbitcleaner.py
```

### Dry run (preview changes without removing)

```bash
uv run qbitcleaner.py --dry-run
```

### Custom config file

```bash
uv run qbitcleaner.py --config my_config.yaml
```

## How It Works

The script:
1. Connects to your qBittorrent instance
2. Fetches all seeding torrents
3. Protects young torrents (under `minimum_seeding_time_days`)
4. Sorts remaining torrents by popularity (lowest first)
5. Removes least popular torrents until `minimum_seeding_torrents` remain
6. Logs all actions for review

## Cleanup Logic

**Protected torrents:**
- Seeding for less than `minimum_seeding_time_days` (default: 14 days)

**Removal order:**
- Torrents are sorted by qBittorrent's popularity metric (ratio / time active in months)
- Least popular torrents are removed first
- Removal stops when `minimum_seeding_torrents` threshold is reached

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
- Keep `config.yaml` private - it contains your credentials
