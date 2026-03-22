"""Tests for torrent categorization."""

from unittest.mock import MagicMock

from qbitcleaner import QBittorrentCleaner


class TestTorrentCategorization:
    """Test torrent categorization functionality."""

    def test_young_torrent_is_protected(self, env_config, mock_torrent, timestamp_10_days_ago):
        """Test that private torrents below minimum seeding time are categorized as young."""
        cleaner = QBittorrentCleaner()
        cleaner.client = MagicMock()
        cleaner.client.torrents_properties = MagicMock(return_value={"is_private": True})
        torrent = mock_torrent(completion_on=timestamp_10_days_ago, is_private=True)

        category, reason = cleaner._categorize_torrent(torrent)

        assert category == "young"
        assert "Young torrent" in reason

    def test_old_torrent_is_removable(self, env_config, mock_torrent, timestamp_20_days_ago):
        """Test that private torrents above minimum seeding time are categorized as removable."""
        cleaner = QBittorrentCleaner()
        cleaner.client = MagicMock()
        cleaner.client.torrents_properties = MagicMock(return_value={"is_private": True})
        torrent = mock_torrent(completion_on=timestamp_20_days_ago, is_private=True)

        category, reason = cleaner._categorize_torrent(torrent)

        assert category == "removable"
        assert "Eligible for removal" in reason

    def test_very_old_torrent_is_removable(self, env_config, mock_torrent, timestamp_110_days_ago):
        """Test that very old private torrents are categorized as removable."""
        cleaner = QBittorrentCleaner()
        cleaner.client = MagicMock()
        cleaner.client.torrents_properties = MagicMock(return_value={"is_private": True})
        torrent = mock_torrent(completion_on=timestamp_110_days_ago, is_private=True)

        category, reason = cleaner._categorize_torrent(torrent)

        assert category == "removable"

    def test_custom_minimum_seeding_time(self, monkeypatch, mock_torrent, timestamp_20_days_ago):
        """Test categorization with custom minimum seeding time."""
        monkeypatch.setenv("QBIT_MINIMUM_SEEDING_TIME_DAYS", "30")

        cleaner = QBittorrentCleaner()
        cleaner.client = MagicMock()
        cleaner.client.torrents_properties = MagicMock(return_value={"is_private": True})
        torrent = mock_torrent(completion_on=timestamp_20_days_ago, is_private=True)  # Only 20 days old

        category, reason = cleaner._categorize_torrent(torrent)

        # Should be young because 20 < 30 days
        assert category == "young"

    def test_torrent_exactly_at_minimum_time(self, env_config, mock_torrent):
        """Test categorization when torrent is exactly at minimum seeding time."""
        from datetime import datetime

        # Create timestamp for exactly 14 days ago
        timestamp_14_days = int((datetime.now().timestamp()) - (14 * 86400))
        cleaner = QBittorrentCleaner()
        cleaner.client = MagicMock()
        cleaner.client.torrents_properties = MagicMock(return_value={"is_private": True})
        torrent = mock_torrent(completion_on=timestamp_14_days, is_private=True)

        category, _reason = cleaner._categorize_torrent(torrent)

        # At exactly 14 days, should be removable (not < 14)
        assert category == "removable"

    def test_public_torrent_always_categorized_as_public(self, env_config, mock_torrent, timestamp_10_days_ago):
        """Test that public (non-private) torrents are always categorized as public."""
        cleaner = QBittorrentCleaner()
        cleaner.client = MagicMock()
        cleaner.client.torrents_properties = MagicMock(return_value={"is_private": False})
        # Even a young torrent should be marked as public if it's not private
        torrent = mock_torrent(completion_on=timestamp_10_days_ago, is_private=False)

        category, reason = cleaner._categorize_torrent(torrent)

        assert category == "public"
        assert "Public torrent" in reason or "non-private" in reason.lower()
