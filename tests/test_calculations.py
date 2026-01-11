"""Tests for seeding time and performance calculations."""

import pytest

from qbitcleaner import QBittorrentCleaner


class TestSeedingTimeCalculation:
    """Test seeding time calculation functionality."""

    def test_calculate_seeding_time_with_completion_on(
        self, config_file, mock_torrent, timestamp_20_days_ago
    ):
        """Test calculating seeding time using completion_on timestamp."""
        cleaner = QBittorrentCleaner(config_file)
        torrent = mock_torrent(completion_on=timestamp_20_days_ago)
        
        days = cleaner._calculate_seeding_time_days(torrent)
        
        assert abs(days - 20.0) < 0.1  # Allow small time difference

    def test_calculate_seeding_time_with_added_on_fallback(
        self, config_file, mock_torrent, timestamp_20_days_ago
    ):
        """Test calculating seeding time using added_on as fallback."""
        cleaner = QBittorrentCleaner(config_file)
        torrent = mock_torrent(completion_on=None, added_on=timestamp_20_days_ago)
        
        days = cleaner._calculate_seeding_time_days(torrent)
        
        assert abs(days - 20.0) < 0.1

    def test_calculate_seeding_time_no_timestamps(self, config_file, mock_torrent):
        """Test calculating seeding time when no timestamps are available."""
        cleaner = QBittorrentCleaner(config_file)
        torrent = mock_torrent(completion_on=None, added_on=None)
        
        days = cleaner._calculate_seeding_time_days(torrent)
        
        assert days == 0.0

    def test_calculate_seeding_time_recent(self, config_file, mock_torrent, timestamp_10_days_ago):
        """Test calculating seeding time for a recently completed torrent."""
        cleaner = QBittorrentCleaner(config_file)
        torrent = mock_torrent(completion_on=timestamp_10_days_ago)
        
        days = cleaner._calculate_seeding_time_days(torrent)
        
        assert abs(days - 10.0) < 0.1


class TestPerformanceValueCalculation:
    """Test performance value calculation functionality."""

    def test_performance_uploaded_gb(self, config_file, mock_torrent):
        """Test calculating performance as uploaded GB."""
        cleaner = QBittorrentCleaner(config_file)
        # 10 GB in bytes
        torrent = mock_torrent(uploaded=10 * (1024 ** 3))
        
        value = cleaner._get_performance_value(torrent)
        
        assert abs(value - 10.0) < 0.01

    def test_performance_uploaded_mb(self, tmp_path, sample_config, mock_torrent):
        """Test calculating performance as uploaded MB."""
        sample_config["cleanup"]["performance_metric"] = "uploaded_mb"
        import yaml
        config_path = tmp_path / "mb_config.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(sample_config, f)
        
        cleaner = QBittorrentCleaner(str(config_path))
        # 100 MB in bytes
        torrent = mock_torrent(uploaded=100 * (1024 ** 2))
        
        value = cleaner._get_performance_value(torrent)
        
        assert abs(value - 100.0) < 0.01

    def test_performance_ratio(self, tmp_path, sample_config, mock_torrent):
        """Test calculating performance as ratio."""
        sample_config["cleanup"]["performance_metric"] = "ratio"
        import yaml
        config_path = tmp_path / "ratio_config.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(sample_config, f)
        
        cleaner = QBittorrentCleaner(str(config_path))
        # 20 GB uploaded, 10 GB downloaded = ratio of 2.0
        torrent = mock_torrent(
            uploaded=20 * (1024 ** 3),
            downloaded=10 * (1024 ** 3)
        )
        
        value = cleaner._get_performance_value(torrent)
        
        assert abs(value - 2.0) < 0.01

    def test_performance_ratio_zero_downloaded(self, tmp_path, sample_config, mock_torrent):
        """Test calculating ratio when downloaded is zero."""
        sample_config["cleanup"]["performance_metric"] = "ratio"
        import yaml
        config_path = tmp_path / "ratio_config.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(sample_config, f)
        
        cleaner = QBittorrentCleaner(str(config_path))
        torrent = mock_torrent(uploaded=10 * (1024 ** 3), downloaded=0)
        
        value = cleaner._get_performance_value(torrent)
        
        assert value == 0.0

    def test_performance_unknown_metric(self, tmp_path, sample_config, mock_torrent):
        """Test calculating performance with unknown metric defaults to uploaded_gb."""
        sample_config["cleanup"]["performance_metric"] = "unknown_metric"
        import yaml
        config_path = tmp_path / "unknown_config.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(sample_config, f)
        
        cleaner = QBittorrentCleaner(str(config_path))
        torrent = mock_torrent(uploaded=5 * (1024 ** 3))
        
        value = cleaner._get_performance_value(torrent)
        
        # Should default to uploaded_gb
        assert abs(value - 5.0) < 0.01
