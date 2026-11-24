"""Application configuration; absent limits never imply hardware ratings."""

from copy import deepcopy
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any


class Config:
    """Load and save independent, validated application settings."""

    _default_config = {
        "timeout": 5000,
        "termination": "\n",
        "retry_attempts": 3,
        "retry_delay": 0.1,
        "default_voltage_range": None,
        "default_current_range": None,
        "safe_limits": {"max_voltage": None, "max_current": None, "max_power": None},
    }

    def __init__(self, config_file: str | Path | None = None, *, allow_missing: bool = False):
        if type(allow_missing) is not bool:
            raise TypeError("allow_missing must be bool")
        self._default_path = config_file is None
        self._allow_missing = self._default_path or allow_missing
        self.config_file = (self._get_default_config_path() if self._default_path
                            else Path(config_file).expanduser())
        self.config = deepcopy(self._default_config)
        self.load_config()

    def _get_default_config_path(self) -> Path:
        return Path.home() / ".config" / "itech_driver" / "config.json"

    @staticmethod
    def _finite(value, name):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"{name} must be a finite real number")
        return value

    @classmethod
    def _validated(cls, supplied):
        if not isinstance(supplied, dict) or not all(isinstance(k, str) for k in supplied):
            raise ValueError("configuration must be a JSON object with string keys")
        result = deepcopy(cls._default_config)
        result.update(deepcopy(supplied))
        limits = supplied.get("safe_limits", {})
        if not isinstance(limits, dict) or set(limits) - set(cls._default_config["safe_limits"]):
            raise ValueError("safe_limits must contain only known limit keys")
        result["safe_limits"] = {**cls._default_config["safe_limits"], **limits}
        if cls._finite(result["timeout"], "timeout") <= 0:
            raise ValueError("timeout must be positive")
        if result["termination"] not in ("\n", "\r\n", "\r"):
            raise ValueError("termination must be LF, CRLF or CR")
        attempts = result["retry_attempts"]
        if type(attempts) is not int or attempts < 1:
            raise ValueError("retry_attempts must be a positive integer")
        if cls._finite(result["retry_delay"], "retry_delay") < 0:
            raise ValueError("retry_delay must be nonnegative")
        for key in ("default_voltage_range", "default_current_range"):
            value = result[key]
            if value is not None:
                if not isinstance(value, (tuple, list)) or len(value) != 2:
                    raise ValueError(f"{key} must be null or a two-element range")
                lo, hi = (cls._finite(v, key) for v in value)
                if lo > hi:
                    raise ValueError(f"{key} minimum exceeds maximum")
                result[key] = (lo, hi)
        for key, value in result["safe_limits"].items():
            if value is not None and cls._finite(value, key) <= 0:
                raise ValueError(f"{key} must be positive or null")
        # Retain JSON-compatible extension keys for callers; never interpret them as ratings.
        json.dumps(result, allow_nan=False)
        return result

    def load_config(self) -> None:
        """Read transactionally; malformed, unreadable and explicit missing files raise."""
        try:
            with self.config_file.open("r", encoding="utf-8") as handle:
                supplied = json.load(handle)
        except FileNotFoundError:
            if self._allow_missing:
                return
            raise
        self.config = self._validated(supplied)

    def save_config(self) -> None:
        """Validate and atomically replace the destination; preserve it on write failure."""
        config = self._validated(self.config)
        if self._default_path:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.config_file.parent,
                                             prefix=f".{self.config_file.name}.", suffix=".tmp", delete=False) as handle:
                temporary = Path(handle.name)
                json.dump(config, handle, indent=2, allow_nan=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.config_file)
        except BaseException as primary:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError as cleanup:
                    if hasattr(primary, "add_note"):
                        primary.add_note(f"temporary file cleanup failed: {cleanup!r}")
                    else:
                        primary.cleanup_error = cleanup
            raise

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        candidate = deepcopy(self.config)
        candidate[key] = value
        self.config = self._validated(candidate)
