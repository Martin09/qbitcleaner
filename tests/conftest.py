"""Pytest configuration and shared fixtures."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
import yaml


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Remove qBittorrent env vars so .env files (auto-loaded by VS Code) don't leak into tests."""
    monkeypatch.delenv("QBIT_URL", raising=False)
    monkeypatch.delenv("QBIT_USERNAME", raising=False)
    monkeypatch.delenv("QBIT_PASSWORD", raising=False)


@pytest.fixture
def sample_config():
    """Create a sample configuration dictionary."""
    return {
        "qbittorrent": {
            "url": "http://localhost:8080",
            "username": "testuser",
            "password": "testpass",
            "verify_ssl": True,
        },
        "cleanup": {
            "minimum_seeding_torrents": 15,
            "minimum_seeding_time_days": 14,
        },
        "logging": {
            "level": "INFO",
            "file": None,
        },
    }


@pytest.fixture
def config_file(tmp_path, sample_config):
    """Create a temporary config file."""
    config_path = tmp_path / "test_config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(sample_config, f)
    return str(config_path)


@pytest.fixture
def mock_torrent():
    """Create a mock torrent object."""

    def _create_torrent(
        name="Test Torrent",
        hash_value="abc123",
        hash=None,  # Allow 'hash' as alias for hash_value
        state="uploading",
        completion_on=None,
        added_on=None,
        uploaded=0,
        downloaded=0,
        num_seeds=10,
        popularity=0.0,
        is_private=True,
    ):
        torrent = MagicMock()
        torrent.name = name
        torrent.hash = hash if hash is not None else hash_value
        torrent.state = state
        torrent.completion_on = completion_on
        torrent.added_on = added_on
        torrent.uploaded = uploaded
        torrent.downloaded = downloaded
        torrent.num_seeds = num_seeds
        torrent.popularity = popularity
        torrent.is_private = is_private
        return torrent

    return _create_torrent


@pytest.fixture
def mock_client():
    """Create a mock qBittorrent client."""
    client = MagicMock()
    client.auth_log_in = MagicMock()
    client.auth_log_out = MagicMock()
    client.torrents_info = MagicMock(return_value=[])
    client.torrents_delete = MagicMock()
    client.torrents_properties = MagicMock(return_value={"is_private": True})
    return client


@pytest.fixture
def timestamp_now():
    """Get current timestamp."""
    return int(datetime.now().timestamp())


@pytest.fixture
def timestamp_15_days_ago():
    """Get timestamp from 15 days ago."""
    return int((datetime.now() - timedelta(days=15)).timestamp())


@pytest.fixture
def timestamp_20_days_ago():
    """Get timestamp from 20 days ago."""
    return int((datetime.now() - timedelta(days=20)).timestamp())


@pytest.fixture
def timestamp_100_days_ago():
    """Get timestamp from 100 days ago."""
    return int((datetime.now() - timedelta(days=100)).timestamp())


@pytest.fixture
def timestamp_110_days_ago():
    """Get timestamp from 110 days ago."""
    return int((datetime.now() - timedelta(days=110)).timestamp())


@pytest.fixture
def timestamp_10_days_ago():
    """Get timestamp from 10 days ago."""
    return int((datetime.now() - timedelta(days=10)).timestamp())
