import unittest
from unittest.mock import patch, MagicMock
from scout_apm_python_logging.otel_logger import (
    OTELLoggingManager,
    initialize_otel_logging,
)


class TestOTELLoggingManager(unittest.TestCase):

    @patch("scout_apm_python_logging.otel_logger.LoggerProvider")
    @patch("scout_apm_python_logging.otel_logger.OTLPLogExporter")
    @patch("scout_apm_python_logging.otel_logger.BatchLogRecordProcessor")
    @patch("scout_apm_python_logging.otel_logger.LoggingHandler")
    @patch("scout_apm_python_logging.otel_logger.set_logger_provider")
    def test_setup_logging(
        self,
        mock_set_logger_provider,
        mock_logging_handler,
        mock_batch_processor,
        mock_otlp_exporter,
        mock_logger_provider,
    ):
        service_name = "test-service"
        manager = OTELLoggingManager(service_name)

        manager.setup_logging()
        manager.shutdown()

        mock_logger_provider.assert_called_once()
        mock_set_logger_provider.assert_called_once()
        mock_otlp_exporter.assert_called_once_with(
            headers={"x-telemetryhub-key": "aaaa-bbbb-cccc-dddd"},
            endpoint="https://otlp.scoutotel.com:4317",
        )
        mock_batch_processor.assert_called_once()
        mock_logging_handler.assert_called_once()

    @patch("scout_apm_python_logging.otel_logger.OTELLoggingManager")
    def test_initialize_otel_logging(self, mock_otel_manager):
        service_name = "test-service"
        mock_manager_instance = MagicMock()
        mock_otel_manager.return_value = mock_manager_instance

        result = initialize_otel_logging(service_name)

        mock_otel_manager.assert_called_once_with(service_name)
        mock_manager_instance.setup_logging.assert_called_once()
        self.assertEqual(result, mock_manager_instance)


if __name__ == "__main__":
    unittest.main()
