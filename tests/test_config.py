"""Tests for configuration loading."""

import tempfile
from pathlib import Path

import pytest
import yaml

from qbitcleaner import QBittorrentCleaner


class TestConfigLoading:
    """Test configuration loading functionality."""

    def test_load_valid_config(self, config_file, sample_config):
        """Test loading a valid configuration file."""
        cleaner = QBittorrentCleaner(config_file)
        assert cleaner.config == sample_config

    def test_load_nonexistent_config(self):
        """Test loading a non-existent configuration file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            QBittorrentCleaner("nonexistent_config.yaml")

    def test_load_invalid_yaml(self, tmp_path):
        """Test loading an invalid YAML file raises YAMLError."""
        invalid_config = tmp_path / "invalid_config.yaml"
        invalid_config.write_text("invalid: yaml: content: [")
        
        with pytest.raises(yaml.YAMLError):
            QBittorrentCleaner(str(invalid_config))

    def test_config_with_defaults(self, tmp_path):
        """Test that missing config values use defaults."""
        minimal_config = {
            "qbittorrent": {
                "host": "localhost",
            }
        }
        config_path = tmp_path / "minimal_config.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(minimal_config, f)
        
        cleaner = QBittorrentCleaner(str(config_path))
        # Should not raise and should have defaults
        assert cleaner.config is not None
        assert cleaner.config.get("qbittorrent", {}).get("host") == "localhost"

    def test_logging_setup(self, config_file):
        """Test that logging is set up correctly."""
        cleaner = QBittorrentCleaner(config_file)
        assert cleaner.logger is not None
        assert cleaner.logger.name == "qbitcleaner"
