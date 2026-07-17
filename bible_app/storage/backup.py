"""Backup helpers for user JSON files and full data snapshots."""

import shutil
from datetime import datetime
from pathlib import Path

from bible_app.config.paths import APP_DIR, BACKUP_DIR
from bible_app.utils.logger import get_logger


logger = get_logger(__name__)


class BackupManager:
    """Create, list, prune, and restore full user-data backups."""

    def __init__(self, backup_dir=BACKUP_DIR, max_backups=10):
        """Create a backup manager.

        Args:
            backup_dir: Preferred directory for backup snapshots.
            max_backups: Maximum number of snapshots to keep.
        """
        self.backup_dir = usable_backup_dir(backup_dir)
        self.max_backups = max(1, int(max_backups))
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, source_dir):
        """Copy a user-data directory into a timestamped backup folder.

        Args:
            source_dir: Directory containing user JSON files and related data.

        Returns:
            Path to the new backup folder, or ``None`` when there is nothing to
            back up yet.
        """
        source_dir = Path(source_dir)
        if not source_dir.exists():
            logger.info("Skipping data backup because source directory does not exist yet: %s", source_dir)
            return None
        if not any(source_dir.iterdir()):
            logger.info("Skipping data backup because source directory is empty: %s", source_dir)
            return None
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = self.backup_dir / f"data-backup-{timestamp}"
        counter = 1
        while backup_path.exists():
            backup_path = self.backup_dir / f"data-backup-{timestamp}-{counter}"
            counter += 1
        shutil.copytree(source_dir, backup_path, ignore=self._ignore_for(source_dir))
        logger.info("Created data backup %s from %s", backup_path, source_dir)
        self.cleanup_old_backups()
        return backup_path

    def restore_backup(self, backup_path, target_dir):
        """Restore a snapshot after validating that it contains JSON data.

        The current target directory is backed up first when it exists, giving
        the user one more recovery point before replacement.

        Args:
            backup_path: Backup folder to restore.
            target_dir: User-data directory to replace.

        Returns:
            The restored target directory path.

        Raises:
            FileNotFoundError: If the backup folder does not exist.
            ValueError: If the backup does not look like app data.
        """
        backup_path = Path(backup_path)
        target_dir = Path(target_dir)
        if not backup_path.exists() or not backup_path.is_dir():
            raise FileNotFoundError(f"Backup not found: {backup_path}")
        if not any(backup_path.rglob("*.json")):
            raise ValueError(f"Backup does not appear to contain JSON data: {backup_path}")

        safety_backup = None
        if target_dir.exists():
            safety_backup = self.create_backup(target_dir)
            shutil.rmtree(target_dir)
        shutil.copytree(backup_path, target_dir)
        logger.info("Restored data backup %s to %s; safety backup=%s", backup_path, target_dir, safety_backup)
        return target_dir

    def list_backups(self):
        """Return known data-backup folders, newest first."""
        if not self.backup_dir.exists():
            return []
        return sorted(
            [path for path in self.backup_dir.iterdir() if path.is_dir() and path.name.startswith("data-backup-")],
            key=lambda path: path.name,
            reverse=True,
        )

    def cleanup_old_backups(self):
        """Delete backups beyond ``max_backups``."""
        backups = self.list_backups()
        for old_backup in backups[self.max_backups:]:
            shutil.rmtree(old_backup)
            logger.info("Removed old data backup %s", old_backup)

    def _ignore_for(self, source_dir):
        ignored_names = {"backups", "logs", "__pycache__"}
        backup_dir = self.backup_dir.resolve()

        def ignore(directory, names):
            directory_path = Path(directory).resolve()
            ignored = set()
            for name in names:
                candidate = directory_path / name
                if name in ignored_names:
                    ignored.add(name)
                    continue
                try:
                    if candidate.resolve() == backup_dir:
                        ignored.add(name)
                except OSError:
                    continue
            return ignored

        return ignore


def usable_backup_dir(preferred=BACKUP_DIR):
    """Return a writable backup directory, falling back to the app folder."""
    for directory in (Path(preferred), APP_DIR / "backups"):
        try:
            directory.mkdir(parents=True, exist_ok=True)
            probe = directory / ".write-test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return directory
        except OSError:
            continue
    return APP_DIR


def backup_file(path, backup_dir=BACKUP_DIR):
    """Create a timestamped copy of a single file if it exists."""
    path = Path(path)
    if not path.exists():
        return
    backup_dir = usable_backup_dir(backup_dir)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{path.stem}-{timestamp}{path.suffix}"
    counter = 1
    while backup_path.exists():
        backup_path = backup_dir / f"{path.stem}-{timestamp}-{counter}{path.suffix}"
        counter += 1
    backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    logger.debug("Backed up %s to %s", path, backup_path)
    return backup_path


def quarantine_file(path, backup_dir=BACKUP_DIR, reason="invalid"):
    """Copy a suspicious file into ``backups/quarantine`` for later review."""
    path = Path(path)
    if not path.exists():
        return None
    quarantine_dir = usable_backup_dir(backup_dir) / "quarantine"
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = quarantine_dir / f"{path.stem}-{reason}-{timestamp}{path.suffix}"
    counter = 1
    while target.exists():
        target = quarantine_dir / f"{path.stem}-{reason}-{timestamp}-{counter}{path.suffix}"
        counter += 1
    shutil.copy2(path, target)
    logger.warning("Quarantined %s to %s", path, target)
    return target
