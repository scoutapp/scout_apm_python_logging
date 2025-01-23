import pytest
import logging
import io
from unittest.mock import patch, MagicMock
from scout_apm_logging.handler import ScoutOtelHandler
from scout_apm.core.tracked_request import Span


@pytest.fixture
def otel_scout_handler():
    # Reset class initialization state
    ScoutOtelHandler._class_initialized = False

    with patch("scout_apm_logging.handler.scout_config") as mock_scout_config, patch(
        "scout_apm_logging.handler.OTLPLogExporter"
    ), patch("scout_apm_logging.handler.LoggerProvider"), patch(
        "scout_apm_logging.handler.BatchLogRecordProcessor"
    ), patch(
        "scout_apm_logging.handler.Resource"
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

    with patch.object(otel_scout_handler, "otel_handler") as mock_otel_handler:
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
        assert record.scout_request_id == "test-id"
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

    with patch.object(otel_scout_handler, "otel_handler") as mock_otel_handler:
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
    assert record.scout_request_id == "test-id"
    assert record.scout_start_time == "2024-03-06T12:00:00"
    assert record.scout_end_time == "2024-03-06T12:00:01"
    assert record.scout_tag_key == "value"
    assert record.controller_entrypoint == "foobar"


@patch("scout_apm_logging.handler.TrackedRequest")
def test_emit_without_scout_request(mock_tracked_request, otel_scout_handler):
    mock_tracked_request.instance.return_value = None
    with patch.object(otel_scout_handler, "otel_handler") as mock_otel_handler:
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
        assert not hasattr(record, "scout_request_id")


def test_emit_already_handling_log(otel_scout_handler):
    with patch.object(otel_scout_handler, "otel_handler") as mock_otel_handler:
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


def test_emit_exception_handling(otel_scout_handler):
    with patch(
        "scout_apm_logging.handler.TrackedRequest"
    ) as mock_tracked_request, patch(
        "sys.stdout", new_callable=io.StringIO
    ) as mock_stdout:

        mock_tracked_request.instance.side_effect = Exception("Test exception")

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

        # Check that the exception was caught and the error message was printed
        assert (
            "Error in ScoutOtelHandler.emit: Test exception" in mock_stdout.getvalue()
        )

    otel_scout_handler._handling_log.value = False


def test_close(otel_scout_handler):
    with patch.object(otel_scout_handler.logger_provider, "shutdown") as mock_shutdown:
        otel_scout_handler.close()
        mock_shutdown.assert_called_once()


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
