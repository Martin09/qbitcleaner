"""Tests for configuration loading from environment variables."""

from qbitcleaner import QBittorrentCleaner


class TestConfigLoading:
    """Test configuration loading from environment variables."""

    def test_defaults_when_no_env_vars(self, sample_config):
        """Test that sensible defaults are used when no env vars are set."""
        cleaner = QBittorrentCleaner()
        assert cleaner.config == sample_config

    def test_env_var_overrides(self, monkeypatch):
        """Test that environment variables are read correctly."""
        monkeypatch.setenv("QBIT_URL", "http://env-host:9090")
        monkeypatch.setenv("QBIT_USERNAME", "env_user")
        monkeypatch.setenv("QBIT_PASSWORD", "env_pass")
        monkeypatch.setenv("QBIT_MINIMUM_SEEDING_TORRENTS", "20")
        monkeypatch.setenv("QBIT_MINIMUM_SEEDING_TIME_DAYS", "7")
        monkeypatch.setenv("QBIT_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("QBIT_LOG_FILE", "/tmp/test.log")

        cleaner = QBittorrentCleaner()
        assert cleaner.config["qbittorrent"]["url"] == "http://env-host:9090"
        assert cleaner.config["qbittorrent"]["username"] == "env_user"
        assert cleaner.config["qbittorrent"]["password"] == "env_pass"
        assert cleaner.config["cleanup"]["minimum_seeding_torrents"] == 20
        assert cleaner.config["cleanup"]["minimum_seeding_time_days"] == 7
        assert cleaner.config["logging"]["level"] == "DEBUG"
        assert cleaner.config["logging"]["file"] == "/tmp/test.log"

    def test_verify_ssl_auto_https(self, monkeypatch):
        """Test that verify_ssl defaults to True for https URLs."""
        monkeypatch.setenv("QBIT_URL", "https://secure-host:8080")
        cleaner = QBittorrentCleaner()
        assert cleaner.config["qbittorrent"]["verify_ssl"] is True

    def test_verify_ssl_auto_http(self, monkeypatch):
        """Test that verify_ssl defaults to False for http URLs."""
        monkeypatch.setenv("QBIT_URL", "http://plain-host:8080")
        cleaner = QBittorrentCleaner()
        assert cleaner.config["qbittorrent"]["verify_ssl"] is False

    def test_verify_ssl_explicit_override(self, monkeypatch):
        """Test that QBIT_VERIFY_SSL can override auto-detection."""
        monkeypatch.setenv("QBIT_URL", "https://secure-host:8080")
        monkeypatch.setenv("QBIT_VERIFY_SSL", "false")
        cleaner = QBittorrentCleaner()
        assert cleaner.config["qbittorrent"]["verify_ssl"] is False

    def test_logging_setup(self):
        """Test that logging is set up correctly."""
        cleaner = QBittorrentCleaner()
        assert cleaner.logger is not None
        assert cleaner.logger.name == "qbitcleaner"
