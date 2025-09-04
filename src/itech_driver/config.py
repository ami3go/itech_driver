"""Configuration management for the power supply driver."""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """Configuration manager for power supply settings."""

    _default_config = {
        "timeout": 5000,
        "termination": "\n",
        "retry_attempts": 3,
        "retry_delay": 0.1,
        "default_voltage_range": (0, 60),
        "default_current_range": (0, 10),
        "safe_limits": {
            "max_voltage": 60,
            "max_current": 10,
            "max_power": 600
        }
    }

    def __init__(self, config_file: Optional[str] = None):
        self.config = self._default_config.copy()
        self.config_file = config_file or self._get_default_config_path()
        self.load_config()

    def _get_default_config_path(self) -> Path:
        """Get default config file path."""
        config_dir = Path.home() / ".config" / "itech_driver"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.json"

    def load_config(self) -> None:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                self.config.update(loaded_config)
            except (json.JSONDecodeError, IOError):
                pass

    def save_config(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except IOError:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self.config[key] = value