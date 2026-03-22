"""Tests for seeding time and helper calculations."""

from qbitcleaner import QBittorrentCleaner


class TestSeedingTimeCalculation:
    """Test seeding time calculation functionality."""

    def test_calculate_seeding_time_with_completion_on(self, mock_torrent, timestamp_20_days_ago):
        """Test calculating seeding time using completion_on timestamp."""
        cleaner = QBittorrentCleaner()
        torrent = mock_torrent(completion_on=timestamp_20_days_ago)

        days = cleaner._calculate_seeding_time_days(torrent)

        assert abs(days - 20.0) < 0.1  # Allow small time difference

    def test_calculate_seeding_time_with_added_on_fallback(self, mock_torrent, timestamp_20_days_ago):
        """Test calculating seeding time using added_on as fallback."""
        cleaner = QBittorrentCleaner()
        torrent = mock_torrent(completion_on=None, added_on=timestamp_20_days_ago)

        days = cleaner._calculate_seeding_time_days(torrent)

        assert abs(days - 20.0) < 0.1

    def test_calculate_seeding_time_no_timestamps(self, mock_torrent):
        """Test calculating seeding time when no timestamps are available."""
        cleaner = QBittorrentCleaner()
        torrent = mock_torrent(completion_on=None, added_on=None)

        days = cleaner._calculate_seeding_time_days(torrent)

        assert days == 0.0

    def test_calculate_seeding_time_recent(self, mock_torrent, timestamp_10_days_ago):
        """Test calculating seeding time for a recently completed torrent."""
        cleaner = QBittorrentCleaner()
        torrent = mock_torrent(completion_on=timestamp_10_days_ago)

        days = cleaner._calculate_seeding_time_days(torrent)

        assert abs(days - 10.0) < 0.1


class TestUploadedGBCalculation:
    """Test uploaded GB calculation functionality."""

    def test_get_uploaded_gb(self, mock_torrent):
        """Test calculating uploaded GB."""
        cleaner = QBittorrentCleaner()
        # 10 GB in bytes
        torrent = mock_torrent(uploaded=10 * (1024**3))

        value = cleaner._get_uploaded_gb(torrent)

        assert abs(value - 10.0) < 0.01

    def test_get_uploaded_gb_zero(self, mock_torrent):
        """Test calculating uploaded GB when zero bytes uploaded."""
        cleaner = QBittorrentCleaner()
        torrent = mock_torrent(uploaded=0)

        value = cleaner._get_uploaded_gb(torrent)

        assert value == 0.0

    def test_get_uploaded_gb_small(self, mock_torrent):
        """Test calculating uploaded GB for small amount."""
        cleaner = QBittorrentCleaner()
        # 512 MB in bytes
        torrent = mock_torrent(uploaded=512 * (1024**2))

        value = cleaner._get_uploaded_gb(torrent)

        assert abs(value - 0.5) < 0.01


class TestPopularityCalculation:
    """Test popularity calculation functionality."""

    def test_get_popularity(self, mock_torrent):
        """Test getting popularity value."""
        cleaner = QBittorrentCleaner()
        torrent = mock_torrent(popularity=5.5)

        value = cleaner._get_popularity(torrent)

        assert abs(value - 5.5) < 0.01

    def test_get_popularity_none(self, mock_torrent):
        """Test getting popularity when None."""
        cleaner = QBittorrentCleaner()
        torrent = mock_torrent(popularity=None)

        value = cleaner._get_popularity(torrent)

        assert value == 0.0

    def test_get_popularity_missing_attribute(self, mock_torrent):
        """Test getting popularity when attribute is missing."""
        cleaner = QBittorrentCleaner()
        torrent = mock_torrent()
        # Remove popularity attribute if it exists
        if hasattr(torrent, "popularity"):
            delattr(torrent, "popularity")

        value = cleaner._get_popularity(torrent)

        assert value == 0.0
