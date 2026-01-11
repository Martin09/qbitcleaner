"""Tests for removal candidate evaluation."""

import pytest

from qbitcleaner import QBittorrentCleaner


class TestRemovalCandidateEvaluation:
    """Test removal candidate evaluation functionality."""

    def test_not_candidate_below_minimum_seeding_time(
        self, config_file, mock_torrent, timestamp_10_days_ago
    ):
        """Test that torrents below minimum seeding time are not candidates."""
        cleaner = QBittorrentCleaner(config_file)
        torrent = mock_torrent(completion_on=timestamp_10_days_ago)
        
        is_candidate, reason, priority = cleaner._is_removal_candidate(torrent)
        
        assert is_candidate is False
        assert "below minimum" in reason
        assert priority == float('inf')

    def test_candidate_exceeds_max_seeding_time(
        self, config_file, mock_torrent, timestamp_110_days_ago
    ):
        """Test that torrents exceeding max seeding time are candidates with highest priority."""
        cleaner = QBittorrentCleaner(config_file)
        torrent = mock_torrent(completion_on=timestamp_110_days_ago)
        
        is_candidate, reason, priority = cleaner._is_removal_candidate(torrent)
        
        assert is_candidate is True
        assert "exceeds maximum" in reason
        assert priority == 0.0  # Highest priority

    def test_candidate_below_performance_threshold(
        self, config_file, mock_torrent, timestamp_20_days_ago
    ):
        """Test that torrents below performance threshold are candidates."""
        cleaner = QBittorrentCleaner(config_file)
        # 5 GB uploaded, threshold is 10 GB
        torrent = mock_torrent(
            completion_on=timestamp_20_days_ago,
            uploaded=5 * (1024 ** 3)
        )
        
        is_candidate, reason, priority = cleaner._is_removal_candidate(torrent)
        
        assert is_candidate is True
        assert "Performance" in reason
        assert priority > 0.0  # Priority based on how far below threshold

    def test_performance_threshold_disabled(
        self, tmp_path, sample_config, mock_torrent, timestamp_20_days_ago
    ):
        """Test that performance threshold check is skipped when set to None."""
        sample_config["cleanup"]["performance_threshold"] = None
        import yaml
        config_path = tmp_path / "no_perf_threshold_config.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(sample_config, f)
        
        cleaner = QBittorrentCleaner(str(config_path))
        # Torrent with low performance but threshold disabled
        torrent = mock_torrent(
            completion_on=timestamp_20_days_ago,
            uploaded=1 * (1024 ** 3)  # Very low upload
        )
        
        is_candidate, reason, priority = cleaner._is_removal_candidate(torrent)
        
        # Should not be candidate - performance check is disabled
        assert is_candidate is False
        assert "Meets all criteria" in reason

    def test_not_candidate_meets_all_criteria(
        self, config_file, mock_torrent, timestamp_20_days_ago
    ):
        """Test that torrents meeting all criteria are not candidates."""
        cleaner = QBittorrentCleaner(config_file)
        # 15 GB uploaded, threshold is 10 GB, seeded for 20 days
        torrent = mock_torrent(
            completion_on=timestamp_20_days_ago,
            uploaded=15 * (1024 ** 3)
        )
        
        is_candidate, reason, priority = cleaner._is_removal_candidate(torrent)
        
        assert is_candidate is False
        assert "Meets all criteria" in reason
        assert priority == float('inf')

    def test_candidate_priority_ordering(
        self, config_file, mock_torrent, timestamp_20_days_ago, timestamp_110_days_ago
    ):
        """Test that candidates are prioritized correctly."""
        cleaner = QBittorrentCleaner(config_file)
        
        # Torrent exceeding max time should have priority 0.0
        torrent_max_time = mock_torrent(completion_on=timestamp_110_days_ago)
        _, _, priority_max = cleaner._is_removal_candidate(torrent_max_time)
        
        # Torrent below threshold should have priority > 0.0
        torrent_low_perf = mock_torrent(
            completion_on=timestamp_20_days_ago,
            uploaded=5 * (1024 ** 3)
        )
        _, _, priority_low = cleaner._is_removal_candidate(torrent_low_perf)
        
        assert priority_max < priority_low

    def test_candidate_with_no_max_seeding_time(
        self, tmp_path, sample_config, mock_torrent, timestamp_110_days_ago
    ):
        """Test that max_seeding_time_days can be disabled (None)."""
        sample_config["cleanup"]["max_seeding_time_days"] = None
        sample_config["cleanup"]["performance_threshold"] = None
        import yaml
        config_path = tmp_path / "no_max_config.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(sample_config, f)
        
        cleaner = QBittorrentCleaner(str(config_path))
        # Torrent with good performance, no max time limit
        torrent = mock_torrent(
            completion_on=timestamp_110_days_ago,
            uploaded=15 * (1024 ** 3)  # Above threshold
        )
        
        is_candidate, reason, priority = cleaner._is_removal_candidate(torrent)
        
        # Should not be candidate - meets all criteria (no max time, no performance threshold)
        assert is_candidate is False
        assert "Meets all criteria" in reason

    def test_candidate_performance_priority_calculation(
        self, config_file, mock_torrent, timestamp_20_days_ago
    ):
        """Test that priority is calculated based on how far below threshold."""
        cleaner = QBittorrentCleaner(config_file)
        
        # 5 GB below threshold (threshold is 10 GB)
        torrent1 = mock_torrent(
            completion_on=timestamp_20_days_ago,
            uploaded=5 * (1024 ** 3)
        )
        _, _, priority1 = cleaner._is_removal_candidate(torrent1)
        
        # 8 GB below threshold
        torrent2 = mock_torrent(
            completion_on=timestamp_20_days_ago,
            uploaded=2 * (1024 ** 3)
        )
        _, _, priority2 = cleaner._is_removal_candidate(torrent2)
        
        # Torrent further below threshold should have higher priority (lower score)
        assert priority2 > priority1
