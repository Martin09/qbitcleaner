"""Pytest configuration and shared fixtures."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Remove all QBIT_ env vars so .env files (auto-loaded by VS Code) don't leak into tests."""
    for var in (
        "QBIT_URL",
        "QBIT_USERNAME",
        "QBIT_PASSWORD",
        "QBIT_VERIFY_SSL",
        "QBIT_MINIMUM_SEEDING_TORRENTS",
        "QBIT_MINIMUM_SEEDING_TIME_DAYS",
        "QBIT_LOG_LEVEL",
        "QBIT_LOG_FILE",
        "QBIT_SCHEDULE",
    ):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def sample_config():
    """Return the expected config dict when default env vars are used."""
    return {
        "qbittorrent": {
            "url": "http://localhost:8080",
            "username": "",
            "password": "",
            "verify_ssl": False,
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
def env_config(monkeypatch):
    """Set standard test env vars and return a helper to set more.

    Explicitly pins all cleanup thresholds so tests don't silently depend on
    the code-level defaults and break whenever those defaults are changed.
    """

    def _set(**kwargs):
        for key, value in kwargs.items():
            monkeypatch.setenv(key, str(value))

    _set(
        QBIT_URL="http://localhost:8080",
        QBIT_USERNAME="testuser",
        QBIT_PASSWORD="testpass",
        QBIT_MINIMUM_SEEDING_TORRENTS="15",
        QBIT_MINIMUM_SEEDING_TIME_DAYS="14",
    )
    return _set


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
