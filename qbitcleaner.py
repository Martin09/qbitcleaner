"""
qBittorrent Cleaner - Automatically clean up seeding torrents based on configurable criteria.

This script connects to a qBittorrent instance and removes torrents based on:
- Age: Protects torrents younger than minimum seeding days
- Popularity: Removes least popular torrents first
- Minimum count: Always maintains a minimum number of seeding torrents
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import urllib3
import yaml
from qbittorrentapi import Client, LoginFailed, APIConnectionError

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class QBittorrentCleaner:
    """Main class for cleaning up qBittorrent seeding list."""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the cleaner with configuration.

        Args:
            config_path: Path to the configuration YAML file.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.client = None

    def _load_config(self, config_path: str) -> Dict:
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to the configuration file.

        Returns:
            Dictionary containing configuration settings.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        return config

    def _setup_logging(self):
        """Set up logging based on configuration."""
        log_level = getattr(logging, self.config.get("logging", {}).get("level", "INFO"))
        log_file = self.config.get("logging", {}).get("file")

        handlers = [logging.StreamHandler(sys.stdout)]
        if log_file:
            handlers.append(logging.FileHandler(log_file))

        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=handlers,
        )

        self.logger = logging.getLogger(__name__)

    def _connect(self) -> bool:
        """
        Connect to qBittorrent instance.

        Returns:
            True if connection successful, False otherwise.
        """
        qb_config = self.config.get("qbittorrent", {})
        url = qb_config.get("url", "http://localhost:8080")
        username = qb_config.get("username", "")
        password = qb_config.get("password", "")
        
        # Automatically detect SSL from URL
        verify_ssl = qb_config.get("verify_ssl", "https" in url.lower())

        self.logger.debug(f"Connecting to qBittorrent at {url} (verify_ssl={verify_ssl})")

        try:
            # Create client with SSL verification setting
            # FORCE_SCHEME_FROM_HOST ensures the correct protocol is used even if SSL fails
            self.client = Client(
                host=url,
                username=username,
                password=password,
                VERIFY_WEBUI_CERTIFICATE=verify_ssl,
                FORCE_SCHEME_FROM_HOST=True
            )
            self.client.auth_log_in()
            self.logger.info(f"Successfully connected to qBittorrent at {url}")
            return True
        except LoginFailed:
            self.logger.error("Failed to authenticate with qBittorrent. Check username/password.")
            return False
        except APIConnectionError as e:
            self.logger.error(f"Failed to connect to qBittorrent: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error connecting to qBittorrent: {e}")
            return False

    def _get_completed_torrents(self) -> List:
        """
        Get list of completed torrents that are currently seeding.

        Returns:
            List of torrent dictionaries.
        """
        try:
            # Get all torrents with seeding status
            # status_filter="seeding" returns all torrents that are seeding (completed and uploading)
            torrents = self.client.torrents_info(status_filter="seeding")
            # All torrents returned by status_filter="seeding" are seeding torrents
            # No need to filter by state - the API already filtered for us
            self.logger.info(f"Found {len(torrents)} seeding torrents")
            return torrents
        except Exception as e:
            self.logger.error(f"Error fetching torrents: {e}")
            return []

    def _calculate_seeding_time_days(self, torrent) -> float:
        """
        Calculate how many days a torrent has been seeding.

        Args:
            torrent: Torrent object from qBittorrent API.

        Returns:
            Number of days the torrent has been seeding.
        """
        completion_time = torrent.completion_on
        if not completion_time:
            # If completion time is not available, use added time as fallback
            completion_time = torrent.added_on

        if not completion_time:
            self.logger.warning(f"Torrent {torrent.name} has no completion time, skipping")
            return 0.0

        completion_date = datetime.fromtimestamp(completion_time)
        seeding_duration = datetime.now() - completion_date
        return seeding_duration.total_seconds() / 86400.0  # Convert to days

    def _get_uploaded_gb(self, torrent) -> float:
        """
        Get uploaded amount in GB for a torrent.

        Args:
            torrent: Torrent object from qBittorrent API.

        Returns:
            Uploaded amount in GB.
        """
        return torrent.uploaded / (1024 ** 3)

    def _get_popularity(self, torrent) -> float:
        """
        Get the popularity value for a torrent.

        Popularity is calculated by qBittorrent as: ratio / time_active (in months).
        Falls back to 0.0 if the popularity attribute is not available.

        Args:
            torrent: Torrent object from qBittorrent API.

        Returns:
            Popularity value (higher = more popular).
        """
        try:
            return float(getattr(torrent, 'popularity', 0.0) or 0.0)
        except (TypeError, ValueError):
            return 0.0

    def _categorize_torrent(self, torrent) -> Tuple[str, str]:
        """
        Categorize a torrent into protected or removable.

        Categories:
        - "young": Torrent is under 14 days old (protected)
        - "removable": Torrent can be removed (ordered by popularity, lowest first)

        Args:
            torrent: Torrent object from qBittorrent API.

        Returns:
            Tuple of (category: str, reason: str).
        """
        cleanup_config = self.config.get("cleanup", {})
        seeding_days = self._calculate_seeding_time_days(torrent)
        min_seeding_days = cleanup_config.get("minimum_seeding_time_days", 14)

        # Rule 1: Protect young torrents (< minimum seeding days)
        if seeding_days < min_seeding_days:
            return "young", f"Young torrent ({seeding_days:.1f} days < {min_seeding_days} days)"

        # Rule 2: Removable - ordered by popularity (lowest first)
        return "removable", "Eligible for removal"

    def cleanup(self, dry_run: bool = False) -> Dict[str, int]:
        """
        Perform cleanup of seeding torrents.

        Args:
            dry_run: If True, only report what would be removed without actually removing.

        Returns:
            Dictionary with statistics about the cleanup operation.
        """
        if not self._connect():
            return {"error": "Failed to connect to qBittorrent"}

        torrents = self._get_completed_torrents()
        cleanup_config = self.config.get("cleanup", {})
        min_seeding_torrents = cleanup_config.get("minimum_seeding_torrents", 15)

        stats = {
            "total_checked": len(torrents),
            "removed": 0,
            "kept": 0,
            "errors": 0,
        }

        self.logger.info(f"Starting cleanup (dry_run={dry_run})...")
        self.logger.info(f"Total seeding torrents: {len(torrents)}, Minimum to keep: {min_seeding_torrents}")

        # Categorize all torrents
        young_torrents = []
        removable_torrents = []

        for torrent in torrents:
            category, reason = self._categorize_torrent(torrent)
            popularity = self._get_popularity(torrent)
            self.logger.debug(
                f"Torrent: {torrent.name[:50]}... | "
                f"Popularity: {popularity:.2f} | Category: {category}"
            )
            if category == "young":
                young_torrents.append((torrent, reason))
            else:
                removable_torrents.append((torrent, reason))

        # Sort removable torrents by popularity (lowest first = remove first)
        removable_torrents.sort(key=lambda x: self._get_popularity(x[0]))

        # Log category counts
        self.logger.info(
            f"Categorized torrents: {len(young_torrents)} young (protected), "
            f"{len(removable_torrents)} eligible for removal"
        )

        # Calculate how many we can remove while maintaining minimum
        current_count = len(torrents)
        
        # We need at least min_seeding_torrents total, including protected ones
        max_removals = max(0, current_count - min_seeding_torrents)
        actual_removals = min(len(removable_torrents), max_removals)

        self.logger.info(
            f"Can remove {actual_removals} of {len(removable_torrents)} eligible torrents "
            f"while maintaining minimum of {min_seeding_torrents} seeding torrents"
        )

        # Remove the least popular torrents (up to the limit)
        for torrent, reason in removable_torrents[:actual_removals]:
            seeding_days = self._calculate_seeding_time_days(torrent)
            uploaded_gb = self._get_uploaded_gb(torrent)
            popularity = self._get_popularity(torrent)

            self.logger.info(
                f"Removing: {torrent.name} "
                f"(Seeding: {seeding_days:.1f} days, "
                f"Uploaded: {uploaded_gb:.2f} GB, "
                f"Popularity: {popularity:.1f})"
            )

            if not dry_run:
                try:
                    self.client.torrents_delete(
                        delete_files=False, torrent_hashes=torrent.hash
                    )
                    stats["removed"] += 1
                except Exception as e:
                    self.logger.error(f"Error removing torrent {torrent.name}: {e}")
                    stats["errors"] += 1
            else:
                stats["removed"] += 1

        # Log protected torrents at DEBUG level
        for torrent, reason in young_torrents:
            self.logger.debug(f"Keeping (young): {torrent.name} - {reason}")

        # Log torrents that couldn't be removed due to minimum threshold
        for torrent, reason in removable_torrents[actual_removals:]:
            popularity = self._get_popularity(torrent)
            self.logger.info(
                f"Keeping (minimum threshold): {torrent.name} "
                f"(Popularity: {popularity:.2f} - would remove but need to maintain minimum)"
            )
            stats["kept"] += 1

        stats["kept"] += len(young_torrents)

        final_count = stats["total_checked"] - stats["removed"]
        self.logger.info(
            f"Cleanup complete. Checked: {stats['total_checked']}, "
            f"Removed: {stats['removed']}, Kept: {stats['kept']}, "
            f"Final seeding count: {final_count}, Errors: {stats['errors']}"
        )

        return stats

    def disconnect(self):
        """Disconnect from qBittorrent instance."""
        if self.client:
            try:
                self.client.auth_log_out()
                self.logger.info("Disconnected from qBittorrent")
            except Exception as e:
                self.logger.warning(f"Error during disconnect: {e}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Clean up qBittorrent seeding list based on configurable criteria"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Perform a dry run without actually removing torrents",
    )

    args = parser.parse_args()

    try:
        cleaner = QBittorrentCleaner(args.config)
        stats = cleaner.cleanup(dry_run=args.dry_run)
        cleaner.disconnect()

        if "error" in stats:
            sys.exit(1)

        sys.exit(0)
    except FileNotFoundError as e:
        logging.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
