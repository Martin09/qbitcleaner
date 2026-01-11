"""Tests for torrent categorization."""

from qbitcleaner import QBittorrentCleaner


class TestTorrentCategorization:
    """Test torrent categorization functionality."""

    def test_young_torrent_is_protected(self, config_file, mock_torrent, timestamp_10_days_ago):
        """Test that torrents below minimum seeding time are categorized as young."""
        cleaner = QBittorrentCleaner(config_file)
        torrent = mock_torrent(completion_on=timestamp_10_days_ago)

        category, reason = cleaner._categorize_torrent(torrent)

        assert category == "young"
        assert "Young torrent" in reason

    def test_old_torrent_is_removable(self, config_file, mock_torrent, timestamp_20_days_ago):
        """Test that torrents above minimum seeding time are categorized as removable."""
        cleaner = QBittorrentCleaner(config_file)
        torrent = mock_torrent(completion_on=timestamp_20_days_ago)

        category, reason = cleaner._categorize_torrent(torrent)

        assert category == "removable"
        assert "Eligible for removal" in reason

    def test_very_old_torrent_is_removable(self, config_file, mock_torrent, timestamp_110_days_ago):
        """Test that very old torrents are categorized as removable."""
        cleaner = QBittorrentCleaner(config_file)
        torrent = mock_torrent(completion_on=timestamp_110_days_ago)

        category, reason = cleaner._categorize_torrent(torrent)

        assert category == "removable"

    def test_custom_minimum_seeding_time(self, tmp_path, sample_config, mock_torrent, timestamp_20_days_ago):
        """Test categorization with custom minimum seeding time."""
        sample_config["cleanup"]["minimum_seeding_time_days"] = 30  # Set to 30 days
        import yaml

        config_path = tmp_path / "custom_min_time_config.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(sample_config, f)

        cleaner = QBittorrentCleaner(str(config_path))
        torrent = mock_torrent(completion_on=timestamp_20_days_ago)  # Only 20 days old

        category, reason = cleaner._categorize_torrent(torrent)

        # Should be young because 20 < 30 days
        assert category == "young"

    def test_torrent_exactly_at_minimum_time(self, tmp_path, sample_config, mock_torrent):
        """Test categorization when torrent is exactly at minimum seeding time."""
        from datetime import datetime

        sample_config["cleanup"]["minimum_seeding_time_days"] = 14
        import yaml

        config_path = tmp_path / "exact_time_config.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(sample_config, f)

        # Create timestamp for exactly 14 days ago
        timestamp_14_days = int((datetime.now().timestamp()) - (14 * 86400))
        cleaner = QBittorrentCleaner(str(config_path))
        torrent = mock_torrent(completion_on=timestamp_14_days)

        category, _reason = cleaner._categorize_torrent(torrent)

        # At exactly 14 days, should be removable (not < 14)
        assert category == "removable"
