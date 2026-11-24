import json
from pathlib import Path

import pytest

from itech_driver.config import Config


def test_missing_default_has_unknown_limits_and_independent_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    a, b = Config(), Config()
    assert not a.config_file.parent.exists()
    assert a.get("default_voltage_range") is None
    assert a.get("default_current_range") is None
    assert all(v is None for v in a.get("safe_limits").values())
    a.get("safe_limits")["max_voltage"] = 12
    assert b.get("safe_limits")["max_voltage"] is None
    assert Config().get("safe_limits")["max_voltage"] is None


def test_explicit_missing_and_roundtrip(tmp_path):
    path = tmp_path / "app.json"
    with pytest.raises(FileNotFoundError):
        Config(str(path))
    c = Config(str(path), allow_missing=True)
    c.set("safe_limits", {"max_voltage": 15})
    c.set("default_current_range", (-3, 5))
    c.set("extension", {"site": "lab"})
    c.save_config()
    restored = Config(path)
    assert restored.get("safe_limits") == {"max_voltage": 15, "max_current": None, "max_power": None}
    assert restored.get("default_current_range") == (-3, 5)
    assert restored.get("extension") == {"site": "lab"}


@pytest.mark.parametrize("content", ["{", "[]", '{"timeout": 0}', '{"safe_limits": {"max_voltage": true}}',
                                     '{"safe_limits": {"max_voltge": 10}}', '{"default_current_range": [5, 1]}',
                                     '{"retry_attempts": 1.5}', '{"safe_limits": {"max_power": NaN}}'])
def test_bad_file_rejected(tmp_path, content):
    path = tmp_path / "config.json"
    path.write_text(content)
    with pytest.raises(ValueError):
        Config(path)


def test_atomic_failure_preserves_file_and_cleans_temp(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text('{"timeout": 1000}')
    c = Config(path)
    c.set("timeout", 2000)
    def fail(*args):
        raise PermissionError("replacement denied")
    monkeypatch.setattr("itech_driver.config.os.replace", fail)
    with pytest.raises(PermissionError):
        c.save_config()
    assert json.loads(path.read_text()) == {"timeout": 1000}
    assert list(tmp_path.iterdir()) == [path]


def test_failed_reload_preserves_settings(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"timeout": 1000}')
    c = Config(path)
    path.write_text('{"timeout": false}')
    with pytest.raises(ValueError):
        c.load_config()
    assert c.get("timeout") == 1000


def test_invalid_public_mutation_cannot_be_saved(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{}')
    c = Config(path)
    c.get("safe_limits")["max_current"] = float("inf")
    with pytest.raises(ValueError):
        c.save_config()
    assert path.read_text() == '{}'


def test_unreadable_explicit_file_propagates(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text('{}')
    original = Path.open
    def denied(self, *args, **kwargs):
        if self == path:
            raise PermissionError("denied")
        return original(self, *args, **kwargs)
    monkeypatch.setattr(Path, "open", denied)
    with pytest.raises(PermissionError):
        Config(path)
