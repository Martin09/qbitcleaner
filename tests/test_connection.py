"""Tests for qBittorrent connection functionality."""

from unittest.mock import MagicMock, patch

import pytest
from qbittorrentapi import APIConnectionError, LoginFailed

from qbitcleaner import QBittorrentCleaner


class TestConnection:
    """Test connection functionality."""

    @patch("qbitcleaner.Client")
    def test_successful_connection(self, mock_client_class, config_file):
        """Test successful connection to qBittorrent."""
        mock_client = MagicMock()
        mock_client.auth_log_in = MagicMock()
        mock_client_class.return_value = mock_client
        
        cleaner = QBittorrentCleaner(config_file)
        result = cleaner._connect()
        
        assert result is True
        assert cleaner.client == mock_client
        mock_client.auth_log_in.assert_called_once()

    @patch("qbitcleaner.Client")
    def test_connection_with_https(self, mock_client_class, tmp_path, sample_config):
        """Test connection with HTTPS enabled."""
        sample_config["qbittorrent"]["url"] = "https://localhost:8080"
        config_path = tmp_path / "https_config.yaml"
        import yaml
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(sample_config, f)
        
        mock_client = MagicMock()
        mock_client.auth_log_in = MagicMock()
        mock_client_class.return_value = mock_client
        
        cleaner = QBittorrentCleaner(str(config_path))
        result = cleaner._connect()
        
        assert result is True
        # Verify HTTPS URL was used
        call_args = mock_client_class.call_args
        assert "https://" in call_args[1]["host"]

    @patch("qbitcleaner.Client")
    def test_connection_with_ssl_verification_disabled(self, mock_client_class, tmp_path, sample_config):
        """Test connection with SSL verification disabled."""
        sample_config["qbittorrent"]["use_https"] = True
        sample_config["qbittorrent"]["verify_ssl"] = False
        config_path = tmp_path / "no_verify_config.yaml"
        import yaml
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(sample_config, f)
        
        mock_client = MagicMock()
        mock_client.auth_log_in = MagicMock()
        mock_client_class.return_value = mock_client
        
        cleaner = QBittorrentCleaner(str(config_path))
        result = cleaner._connect()
        
        assert result is True
        # Verify VERIFY_WEBUI_CERTIFICATE was set to False
        call_args = mock_client_class.call_args
        assert call_args[1]["VERIFY_WEBUI_CERTIFICATE"] is False

    @patch("qbitcleaner.Client")
    def test_connection_with_path_in_url(self, mock_client_class, tmp_path, sample_config):
        """Test connection when URL includes a path."""
        sample_config["qbittorrent"]["url"] = "https://ds218.local:8080/qbittorrent"
        config_path = tmp_path / "path_url_config.yaml"
        import yaml
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(sample_config, f)
        
        mock_client = MagicMock()
        mock_client.auth_log_in = MagicMock()
        mock_client_class.return_value = mock_client
        
        cleaner = QBittorrentCleaner(str(config_path))
        result = cleaner._connect()
        
        assert result is True
        # Verify URL is used directly
        call_args = mock_client_class.call_args
        url = call_args[1]["host"]
        assert url == "https://ds218.local:8080/qbittorrent"

    @patch("qbitcleaner.Client")
    def test_connection_auto_detects_ssl_from_url(self, mock_client_class, tmp_path, sample_config):
        """Test that SSL verification is auto-detected from URL."""
        sample_config["qbittorrent"]["url"] = "https://localhost:8080"
        # Don't set verify_ssl - should default based on URL
        if "verify_ssl" in sample_config["qbittorrent"]:
            del sample_config["qbittorrent"]["verify_ssl"]
        config_path = tmp_path / "auto_ssl_config.yaml"
        import yaml
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(sample_config, f)
        
        mock_client = MagicMock()
        mock_client.auth_log_in = MagicMock()
        mock_client_class.return_value = mock_client
        
        cleaner = QBittorrentCleaner(str(config_path))
        result = cleaner._connect()
        
        assert result is True
        # Verify SSL verification is enabled (default for https)
        call_args = mock_client_class.call_args
        assert call_args[1]["VERIFY_WEBUI_CERTIFICATE"] is True

    @patch("qbitcleaner.Client")
    def test_login_failed(self, mock_client_class, config_file):
        """Test handling of login failure."""
        mock_client = MagicMock()
        mock_client.auth_log_in.side_effect = LoginFailed()
        mock_client_class.return_value = mock_client
        
        cleaner = QBittorrentCleaner(config_file)
        result = cleaner._connect()
        
        assert result is False
        assert cleaner.client == mock_client

    @patch("qbitcleaner.Client")
    def test_connection_error(self, mock_client_class, config_file):
        """Test handling of connection error."""
        mock_client_class.side_effect = APIConnectionError("Connection failed")
        
        cleaner = QBittorrentCleaner(config_file)
        result = cleaner._connect()
        
        assert result is False

    @patch("qbitcleaner.Client")
    def test_unexpected_error(self, mock_client_class, config_file):
        """Test handling of unexpected connection error."""
        mock_client_class.side_effect = Exception("Unexpected error")
        
        cleaner = QBittorrentCleaner(config_file)
        result = cleaner._connect()
        
        assert result is False

    def test_disconnect(self, config_file, mock_client):
        """Test disconnecting from qBittorrent."""
        cleaner = QBittorrentCleaner(config_file)
        cleaner.client = mock_client
        
        cleaner.disconnect()
        
        mock_client.auth_log_out.assert_called_once()

    def test_disconnect_no_client(self, config_file):
        """Test disconnect when no client is connected."""
        cleaner = QBittorrentCleaner(config_file)
        cleaner.client = None
        
        # Should not raise an error
        cleaner.disconnect()

    def test_disconnect_error(self, config_file, mock_client):
        """Test disconnect handles errors gracefully."""
        mock_client.auth_log_out.side_effect = Exception("Disconnect error")
        
        cleaner = QBittorrentCleaner(config_file)
        cleaner.client = mock_client
        
        # Should not raise, just log warning
        cleaner.disconnect()
