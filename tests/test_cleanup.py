"""Tests for cleanup functionality."""

from unittest.mock import MagicMock, patch

import pytest

from qbitcleaner import QBittorrentCleaner


class TestGetCompletedTorrents:
    """Test getting completed torrents."""

    @patch("qbitcleaner.Client")
    def test_get_completed_torrents(self, mock_client_class, config_file, mock_torrent):
        """Test getting list of completed seeding torrents."""
        mock_client = MagicMock()
        mock_client.auth_log_in = MagicMock()
        
        # Create mock torrents - status_filter="seeding" already filters, so all returned are seeding
        seeding_torrent1 = mock_torrent(name="Seeding Torrent 1", state="uploading")
        seeding_torrent2 = mock_torrent(name="Seeding Torrent 2", state="stalledUP")
        mock_client.torrents_info.return_value = [seeding_torrent1, seeding_torrent2]
        mock_client_class.return_value = mock_client
        
        cleaner = QBittorrentCleaner(config_file)
        cleaner.client = mock_client
        
        torrents = cleaner._get_completed_torrents()
        
        assert len(torrents) == 2
        assert torrents[0].name == "Seeding Torrent 1"
        assert torrents[1].name == "Seeding Torrent 2"

    @patch("qbitcleaner.Client")
    def test_get_completed_torrents_empty(self, mock_client_class, config_file):
        """Test getting torrents when none are seeding."""
        mock_client = MagicMock()
        mock_client.auth_log_in = MagicMock()
        mock_client.torrents_info.return_value = []
        mock_client_class.return_value = mock_client
        
        cleaner = QBittorrentCleaner(config_file)
        cleaner.client = mock_client
        
        torrents = cleaner._get_completed_torrents()
        
        assert len(torrents) == 0

    @patch("qbitcleaner.Client")
    def test_get_completed_torrents_error(self, mock_client_class, config_file):
        """Test handling error when fetching torrents."""
        mock_client = MagicMock()
        mock_client.auth_log_in = MagicMock()
        mock_client.torrents_info.side_effect = Exception("API Error")
        mock_client_class.return_value = mock_client
        
        cleaner = QBittorrentCleaner(config_file)
        cleaner.client = mock_client
        
        torrents = cleaner._get_completed_torrents()
        
        assert len(torrents) == 0


class TestCleanup:
    """Test cleanup functionality."""

    @patch("qbitcleaner.Client")
    def test_cleanup_dry_run(self, mock_client_class, config_file, mock_torrent, timestamp_20_days_ago):
        """Test cleanup in dry-run mode."""
        mock_client = MagicMock()
        mock_client.auth_log_in = MagicMock()
        
        # Create 20 torrents, 10 below threshold
        torrents = []
        for i in range(20):
            uploaded = 5 * (1024 ** 3) if i < 10 else 15 * (1024 ** 3)
            torrents.append(mock_torrent(
                name=f"Torrent {i}",
                hash=f"hash{i}",
                completion_on=timestamp_20_days_ago,
                uploaded=uploaded
            ))
        
        mock_client.torrents_info.return_value = torrents
        mock_client_class.return_value = mock_client
        
        cleaner = QBittorrentCleaner(config_file)
        stats = cleaner.cleanup(dry_run=True)
        
        # Should remove 5 (20 total - 15 minimum = 5 can be removed)
        assert stats["total_checked"] == 20
        assert stats["removed"] == 5
        assert stats["kept"] == 15
        assert stats["errors"] == 0
        # Should not actually call delete
        mock_client.torrents_delete.assert_not_called()

    @patch("qbitcleaner.Client")
    def test_cleanup_actual_removal(self, mock_client_class, config_file, mock_torrent, timestamp_20_days_ago):
        """Test cleanup with actual removal."""
        mock_client = MagicMock()
        mock_client.auth_log_in = MagicMock()
        
        # Create 20 torrents, 10 below threshold
        torrents = []
        for i in range(20):
            uploaded = 5 * (1024 ** 3) if i < 10 else 15 * (1024 ** 3)
            torrents.append(mock_torrent(
                name=f"Torrent {i}",
                hash=f"hash{i}",
                completion_on=timestamp_20_days_ago,
                uploaded=uploaded
            ))
        
        mock_client.torrents_info.return_value = torrents
        mock_client_class.return_value = mock_client
        
        cleaner = QBittorrentCleaner(config_file)
        stats = cleaner.cleanup(dry_run=False)
        
        # Should remove 5
        assert stats["removed"] == 5
        # Should call delete 5 times
        assert mock_client.torrents_delete.call_count == 5

    @patch("qbitcleaner.Client")
    def test_cleanup_maintains_minimum(self, mock_client_class, config_file, mock_torrent, timestamp_20_days_ago):
        """Test that cleanup maintains minimum seeding torrents."""
        mock_client = MagicMock()
        mock_client.auth_log_in = MagicMock()
        
        # Create exactly 15 torrents, all below threshold
        torrents = []
        for i in range(15):
            torrents.append(mock_torrent(
                name=f"Torrent {i}",
                hash=f"hash{i}",
                completion_on=timestamp_20_days_ago,
                uploaded=5 * (1024 ** 3)  # All below threshold
            ))
        
        mock_client.torrents_info.return_value = torrents
        mock_client_class.return_value = mock_client
        
        cleaner = QBittorrentCleaner(config_file)
        stats = cleaner.cleanup(dry_run=False)
        
        # Should not remove any (need to maintain minimum of 15)
        assert stats["total_checked"] == 15
        assert stats["removed"] == 0
        assert stats["kept"] == 15
        mock_client.torrents_delete.assert_not_called()

    @patch("qbitcleaner.Client")
    def test_cleanup_removes_max_time_first(
        self, mock_client_class, config_file, mock_torrent, timestamp_20_days_ago, timestamp_110_days_ago
    ):
        """Test that torrents exceeding max time are removed first."""
        mock_client = MagicMock()
        mock_client.auth_log_in = MagicMock()
        
        # Create 20 torrents: 5 exceed max time, 5 below threshold, 10 good
        torrents = []
        for i in range(5):
            torrents.append(mock_torrent(
                name=f"Old Torrent {i}",
                hash=f"old{i}",
                completion_on=timestamp_110_days_ago,
                uploaded=15 * (1024 ** 3)
            ))
        for i in range(5):
            torrents.append(mock_torrent(
                name=f"Low Perf {i}",
                hash=f"low{i}",
                completion_on=timestamp_20_days_ago,
                uploaded=5 * (1024 ** 3)
            ))
        for i in range(10):
            torrents.append(mock_torrent(
                name=f"Good {i}",
                hash=f"good{i}",
                completion_on=timestamp_20_days_ago,
                uploaded=15 * (1024 ** 3)
            ))
        
        mock_client.torrents_info.return_value = torrents
        mock_client_class.return_value = mock_client
        
        cleaner = QBittorrentCleaner(config_file)
        stats = cleaner.cleanup(dry_run=False)
        
        # Should remove 5 (20 - 15 minimum)
        # Should prioritize old torrents first
        assert stats["removed"] == 5
        # Check that old torrents were removed (they have priority 0.0)
        delete_calls = [call[1]["torrent_hashes"] for call in mock_client.torrents_delete.call_args_list]
        assert all(hash.startswith("old") for hash in delete_calls)

    @patch("qbitcleaner.Client")
    def test_cleanup_connection_failure(self, mock_client_class, config_file):
        """Test cleanup when connection fails."""
        mock_client_class.side_effect = Exception("Connection failed")
        
        cleaner = QBittorrentCleaner(config_file)
        stats = cleaner.cleanup()
        
        assert "error" in stats
        assert stats["error"] == "Failed to connect to qBittorrent"

    @patch("qbitcleaner.Client")
    def test_cleanup_removal_error(self, mock_client_class, config_file, mock_torrent, timestamp_20_days_ago):
        """Test cleanup handles removal errors gracefully."""
        mock_client = MagicMock()
        mock_client.auth_log_in = MagicMock()
        mock_client.torrents_delete.side_effect = Exception("Delete failed")
        
        # Create 20 torrents, 10 below threshold
        torrents = []
        for i in range(20):
            uploaded = 5 * (1024 ** 3) if i < 10 else 15 * (1024 ** 3)
            torrents.append(mock_torrent(
                name=f"Torrent {i}",
                hash=f"hash{i}",
                completion_on=timestamp_20_days_ago,
                uploaded=uploaded
            ))
        
        mock_client.torrents_info.return_value = torrents
        mock_client_class.return_value = mock_client
        
        cleaner = QBittorrentCleaner(config_file)
        stats = cleaner.cleanup(dry_run=False)
        
        # Should track errors
        assert stats["errors"] == 5  # All 5 removals failed
        assert stats["removed"] == 0  # None actually removed

    @patch("qbitcleaner.Client")
    def test_cleanup_empty_torrent_list(self, mock_client_class, config_file):
        """Test cleanup with no torrents."""
        mock_client = MagicMock()
        mock_client.auth_log_in = MagicMock()
        mock_client.torrents_info.return_value = []
        mock_client_class.return_value = mock_client
        
        cleaner = QBittorrentCleaner(config_file)
        stats = cleaner.cleanup()
        
        assert stats["total_checked"] == 0
        assert stats["removed"] == 0
        assert stats["kept"] == 0

    @patch("qbitcleaner.Client")
    def test_cleanup_all_below_minimum_time(
        self, mock_client_class, config_file, mock_torrent, timestamp_10_days_ago
    ):
        """Test cleanup when all torrents are below minimum seeding time."""
        mock_client = MagicMock()
        mock_client.auth_log_in = MagicMock()
        
        # Create 20 torrents, all seeded for only 10 days (below 15 day minimum)
        torrents = []
        for i in range(20):
            torrents.append(mock_torrent(
                name=f"Torrent {i}",
                hash=f"hash{i}",
                completion_on=timestamp_10_days_ago,
                uploaded=5 * (1024 ** 3)
            ))
        
        mock_client.torrents_info.return_value = torrents
        mock_client_class.return_value = mock_client
        
        cleaner = QBittorrentCleaner(config_file)
        stats = cleaner.cleanup()
        
        # Should not remove any (all below minimum time)
        assert stats["removed"] == 0
        assert stats["kept"] == 20
        mock_client.torrents_delete.assert_not_called()
