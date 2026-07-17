"""JSON persistence helpers."""

import json
import os
from pathlib import Path

from bible_app.storage.backup import backup_file, quarantine_file
from bible_app.utils.logger import get_logger


logger = get_logger(__name__)


def read_json(path, fallback, validator=None):
    """Read JSON safely, optionally validating the loaded payload.

    Invalid files are copied into the quarantine folder before the fallback is
    returned. This protects user data from being overwritten silently while the
    app continues to open.

    Args:
        path: JSON file path.
        fallback: Value returned when the file is missing or invalid.
        validator: Optional callable that normalizes or rejects the payload.

    Returns:
        Loaded and validated JSON data, or ``fallback``.
    """
    path = Path(path)
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if validator:
                payload = validator(payload)
            return payload
        except Exception as exc:
            quarantine_file(path, reason="invalid-json")
            logger.warning("Could not read valid JSON from %s; quarantined file and using fallback. Error: %s", path, exc)
            return fallback
    return fallback


def write_json(path, payload, make_backup=True, validator=None):
    """Write JSON atomically, with optional backup and validation.

    Args:
        path: Destination JSON file path.
        payload: JSON-serializable value to save.
        make_backup: Whether to save a timestamped copy of an existing file.
        validator: Optional callable that normalizes or rejects the payload
            before it is written.

    Returns:
        None.

    Raises:
        ValueError: If the validator rejects the payload.
        OSError: If the file cannot be written.
    """
    path = Path(path)
    if validator:
        payload = validator(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    if make_backup:
        backup_file(path)
    logger.debug("Writing JSON to %s", path)
    temp_path = path.with_name(f"{path.name}.tmp")
    temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(temp_path, path)
