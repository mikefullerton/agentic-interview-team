"""Tests for oslog observer — system log writer."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

OBSERVERS_DIR = Path(__file__).parent.parent.parent / "plugins" / "dev-team" / "scripts" / "observers"
sys.path.insert(0, str(OBSERVERS_DIR))


def test_oslog_formats_message_correctly(sample_event):
    import oslog

    msg = oslog.format_message(sample_event)
    assert "[dev-team]" in msg
    assert "general-purpose" in msg
    assert "Implement Task 4" in msg
    assert "completed" in msg
    assert "45s" in msg
    assert "16 calls" in msg


def test_oslog_formats_short_description(sample_event):
    import oslog

    sample_event["agent_description"] = ""
    msg = oslog.format_message(sample_event)
    assert "general-purpose" in msg


def test_oslog_calls_logger(sample_event):
    import oslog

    with patch("oslog.subprocess.run") as mock_run:
        oslog.observe(sample_event)
        mock_run.assert_called_once()
        args = mock_run.call_args
        cmd = args[0][0]
        assert cmd[0] == "logger"
        assert "-t" in cmd
        assert "dev-team" in cmd


def test_oslog_silently_handles_missing_logger(sample_event):
    import oslog

    with patch("oslog.subprocess.run", side_effect=FileNotFoundError):
        oslog.observe(sample_event)


def test_oslog_silently_handles_timeout(sample_event):
    import oslog
    import subprocess

    with patch("oslog.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="logger", timeout=5)):
        oslog.observe(sample_event)
