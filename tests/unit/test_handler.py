import io
import logging
from unittest.mock import MagicMock, patch

import pytest
from scout_apm.core.tracked_request import Span

from scout_apm_logging.handler import ScoutOtelHandler


@pytest.fixture
def otel_scout_handler():
    # Reset class initialization state
    ScoutOtelHandler.otel_handler = None

    with (
        patch("scout_apm_logging.handler.scout_config") as mock_scout_config,
        patch("scout_apm_logging.handler.OTLPLogExporter"),
        patch("scout_apm_logging.handler.LoggerProvider"),
        patch("scout_apm_logging.handler.BatchLogRecordProcessor"),
        patch("scout_apm_logging.handler.Resource"),
    ):
        mock_scout_config.value.return_value = "test-ingest-key"
        handler = ScoutOtelHandler(service_name="test-service")
        # Force initialization
        handler._initialize()
        return handler


def test_init(otel_scout_handler):
    assert otel_scout_handler.service_name == "test-service"
    assert otel_scout_handler.ingest_key is not None
    assert otel_scout_handler.endpoint is not None


@patch("scout_apm_logging.handler.TrackedRequest")
def test_emit_with_scout_request(mock_tracked_request, otel_scout_handler):
    mock_request = MagicMock()
    mock_request.request_id = "test-id"
    mock_request.start_time.isoformat.return_value = "2024-03-06T12:00:00"
    mock_request.end_time.isoformat.return_value = "2024-03-06T12:00:01"
    mock_request.tags = {"key": "value"}
    mock_request.operation = None
    mock_request.complete_spans = [
        Span(mock_request.id, "Middleware"),
        Span(mock_request.id, "Controller/foobar"),
    ]
    mock_tracked_request.instance.return_value = mock_request

    with patch.object(ScoutOtelHandler, "otel_handler") as mock_otel_handler:
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        otel_scout_handler.emit(record)

        mock_otel_handler.emit.assert_called_once()
        assert record.scout_transaction_id == "test-id"
        assert record.scout_start_time == "2024-03-06T12:00:00"
        assert record.scout_end_time == "2024-03-06T12:00:01"
        assert record.scout_tag_key == "value"
        assert record.controller_entrypoint == "foobar"


@patch("scout_apm_logging.handler.TrackedRequest")
def test_emit_when_scout_request_contains_operation(
    mock_tracked_request, otel_scout_handler
):
    mock_request = MagicMock()
    mock_request.request_id = "test-id"
    mock_request.start_time.isoformat.return_value = "2024-03-06T12:00:00"
    mock_request.end_time.isoformat.return_value = "2024-03-06T12:00:01"
    mock_request.tags = {"key": "value"}
    mock_request.complete_spans = [
        Span(mock_request.id, "Middleware"),
    ]
    mock_request.operation = MagicMock().return_value = "Controller/foobar"
    mock_tracked_request.instance.return_value = mock_request

    with patch.object(ScoutOtelHandler, "otel_handler") as mock_otel_handler:
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        otel_scout_handler.emit(record)

    mock_otel_handler.emit.assert_called_once()
    assert record.scout_transaction_id == "test-id"
    assert record.scout_start_time == "2024-03-06T12:00:00"
    assert record.scout_end_time == "2024-03-06T12:00:01"
    assert record.scout_tag_key == "value"
    assert record.controller_entrypoint == "foobar"


@patch("scout_apm_logging.handler.TrackedRequest")
def test_emit_without_scout_request(mock_tracked_request, otel_scout_handler):
    mock_tracked_request.instance.return_value = None
    with patch.object(ScoutOtelHandler, "otel_handler") as mock_otel_handler:
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        otel_scout_handler.emit(record)

        mock_otel_handler.emit.assert_called_once()
        assert not hasattr(record, "scout_transaction_id")


def test_emit_already_handling_log(otel_scout_handler):
    with patch.object(ScoutOtelHandler, "otel_handler") as mock_otel_handler:
        # Simulate that we're already handling a log message
        otel_scout_handler._handling_log.value = True

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        otel_scout_handler.emit(record)

        mock_otel_handler.emit.assert_called_once_with(record)

    otel_scout_handler._handling_log.value = False


@patch("scout_apm_logging.handler.TrackedRequest")
def test_emit_resets_handling_log_on_exception(
    mock_tracked_request, otel_scout_handler
):
    """Verify _handling_log.value is reset even when an exception occurs during emit."""
    mock_tracked_request.instance.side_effect = RuntimeError("Test exception")

    with patch.object(ScoutOtelHandler, "otel_handler"):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        with pytest.raises(RuntimeError, match="Test exception"):
            otel_scout_handler.emit(record)

        # The key assertion: _handling_log should be reset to False
        assert otel_scout_handler._handling_log.value is False


@patch("scout_apm_logging.handler.scout_config")
def test_get_service_name(mock_scout_config, otel_scout_handler):
    mock_scout_config.value.return_value = "scout-service"
    assert otel_scout_handler._get_service_name(None) == "scout-service"
    assert (
        otel_scout_handler._get_service_name("provided-service") == "provided-service"
    )
    mock_scout_config.value.return_value = None
    assert otel_scout_handler._get_service_name(None) == "unnamed-service"


@patch("scout_apm_logging.handler.scout_config")
def test_get_endpoint(mock_scout_config, otel_scout_handler):
    mock_scout_config.value.return_value = "custom.endpoint:1234"
    assert otel_scout_handler._get_endpoint() == "custom.endpoint:1234"


@patch("scout_apm_logging.handler.scout_config")
def test_get_ingest_key(mock_scout_config, otel_scout_handler):
    mock_scout_config.value.return_value = "test-ingest-key"
    assert otel_scout_handler._get_ingest_key() == "test-ingest-key"


@patch("scout_apm_logging.handler.scout_config")
def test_get_ingest_key_not_set(mock_scout_config, otel_scout_handler):
    mock_scout_config.value.return_value = None
    with pytest.raises(ValueError, match="SCOUT_LOGS_INGEST_KEY is not set"):
        otel_scout_handler._get_ingest_key()


def test_initialize_only_once(otel_scout_handler):
    # First initialization happens in fixture
    initial_service_name = otel_scout_handler.service_name

    # Try to initialize again
    otel_scout_handler._initialize()

    # Service name should not change since second initialization should return early
    assert otel_scout_handler.service_name == initial_service_name


def test_emit_handles_initialization_failure():
    with patch("scout_apm_logging.handler.scout_config") as mock_scout_config:
        mock_scout_config.value.return_value = (
            None  # This will cause _get_ingest_key to fail
        )
        ScoutOtelHandler.otel_handler = None

        handler = ScoutOtelHandler(service_name="test-service")

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="Test message",
                args=(),
                exc_info=None,
            )
            handler.emit(record)

            assert (
                "Failed to initialize ScoutOtelHandler: "
                "SCOUT_LOGS_INGEST_KEY is not set" in mock_stdout.getvalue()
            )
