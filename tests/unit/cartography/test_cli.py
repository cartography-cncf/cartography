import io
import logging
import re

from cartography.cli import _apply_timestamp_log_format


def test_apply_timestamp_log_format_prepends_timestamp_and_level():
    """
    _apply_timestamp_log_format() should install a formatter on the root logger's
    handlers so that emitted lines carry an ISO-8601 timestamp, the level, and the
    logger name (issue #1213).
    """
    # Arrange: attach our own handler to the root logger, remembering original
    # formatters of any pre-existing handlers so the test leaves no trace.
    root = logging.getLogger()
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    original_formatters = [(h, h.formatter) for h in root.handlers]
    root.addHandler(handler)
    test_logger = logging.getLogger("cartography.test_cli")
    original_level = root.level
    root.setLevel(logging.INFO)

    try:
        # Act
        _apply_timestamp_log_format()
        test_logger.info("hello from the test")
        output = stream.getvalue()
    finally:
        root.removeHandler(handler)
        root.setLevel(original_level)
        for h, fmt in original_formatters:
            h.setFormatter(fmt)

    # Assert: ISO-8601 timestamp, level, and logger name precede the message.
    assert re.match(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[+-]\d{4})? "
        r"INFO cartography\.test_cli: hello from the test$",
        output.strip(),
    ), f"unexpected log line: {output!r}"


def test_default_handlers_untouched_without_flag():
    """
    Without calling _apply_timestamp_log_format(), a handler keeps whatever
    formatter it had (None by default), preserving the existing log format.
    """
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    assert handler.formatter is None
