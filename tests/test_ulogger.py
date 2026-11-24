import logging

import pytest

from itech_driver.utils.ulogger import setup_logging


@pytest.fixture
def isolated_logger(monkeypatch):
    logger = logging.Logger("itech_driver")
    original = logging.getLogger
    monkeypatch.setattr(logging, "getLogger", lambda name=None: logger if name == "itech_driver" else original(name))
    try:
        yield logger
    finally:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()


def test_reconfigure_closes_owned_file_preserves_foreign(tmp_path, isolated_logger):
    logger = isolated_logger
    foreign = logging.NullHandler()
    logger.addHandler(foreign)
    old_path = tmp_path / "old.log"
    new_path = tmp_path / "new.log"
    setup_logging(log_file=old_path)
    old_file = next(h for h in logger.handlers if isinstance(h, logging.FileHandler))
    logger.info("first")
    setup_logging(log_file=new_path)
    assert foreign in logger.handlers
    assert old_file not in logger.handlers
    assert old_file.stream is None
    assert len(logger.handlers) == 3
    old_path.rename(tmp_path / "renamed.log")
    logger.info("second")
    assert (tmp_path / "renamed.log").read_text().count("first") == 1
    assert new_path.read_text().count("second") == 1
    setup_logging()
    assert logger.handlers[0] is foreign
    assert len(logger.handlers) == 2
    new_path.unlink()


def test_failed_new_file_keeps_old_handlers(tmp_path, isolated_logger):
    logger = isolated_logger
    setup_logging(log_file=tmp_path / "valid.log")
    previous = list(logger.handlers)
    with pytest.raises(OSError):
        setup_logging(logging.DEBUG, tmp_path / "missing" / "invalid.log")
    assert logger.handlers == previous
    assert logger.level == logging.INFO
    logger.info("still live")
    assert "still live" in (tmp_path / "valid.log").read_text()
