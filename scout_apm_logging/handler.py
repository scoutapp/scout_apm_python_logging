import logging
import os
import threading

from opentelemetry import _logs
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from scout_apm.core import scout_config
from scout_apm.core.tracked_request import TrackedRequest

from scout_apm_logging.utils.operation_utils import get_operation_detail


class ScoutOtelHandler(logging.Handler):
    _initialization_lock = threading.Lock()
    otel_handler = None

    def __init__(self, service_name):
        super().__init__()
        self.logger_provider = None
        self.service_name = service_name
        self._handling_log = threading.local()

    def _initialize(self):
        with self._initialization_lock:
            if ScoutOtelHandler.otel_handler:
                return

            self.service_name = self._get_service_name(self.service_name)
            self.ingest_key = self._get_ingest_key()
            self.endpoint = self._get_endpoint()
            self.setup_otel_handler()

    def setup_otel_handler(self):
        self.logger_provider = LoggerProvider(
            resource=Resource.create(
                {
                    "service.name": self.service_name,
                    "service.instance.id": os.uname().nodename,
                }
            )
        )
        _logs.set_logger_provider(self.logger_provider)

        otlp_exporter = OTLPLogExporter(
            headers={"x-scout-key": self.ingest_key},
            endpoint=self.endpoint,
        )
        self.logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(otlp_exporter)
        )

        ScoutOtelHandler.otel_handler = LoggingHandler(
            level=logging.NOTSET, logger_provider=self.logger_provider
        )

    def emit(self, record):
        if not ScoutOtelHandler.otel_handler:
            try:
                self._initialize()
            except Exception as e:
                print(f"Failed to initialize ScoutOtelHandler: {e}")
                return

        if getattr(self._handling_log, "value", False):
            # We're already handling a log message, don't get the TrackedRequest
            return ScoutOtelHandler.otel_handler.emit(record)
        try:
            self._handling_log.value = True
            scout_request = TrackedRequest.instance()

            if scout_request:
                operation_detail = get_operation_detail(scout_request)
                if operation_detail:
                    setattr(
                        record,
                        operation_detail.entrypoint_attribute,
                        operation_detail.name,
                    )

                # Add Scout-specific attributes to the log record
                record.scout_transaction_id = scout_request.request_id
                record.scout_start_time = scout_request.start_time.isoformat()
                # Add duration if the request is completed
                if scout_request.end_time:
                    record.scout_end_time = scout_request.end_time.isoformat()
                    record.scout_duration = (
                        scout_request.end_time - scout_request.start_time
                    ).total_seconds()

                setattr(record, "service.name", self.service_name)

                # Add tags
                for key, value in scout_request.tags.items():
                    setattr(record, f"scout_tag_{key}", value)

                # Add the current span's operation if available
                current_span = scout_request.current_span()
                if current_span:
                    record.scout_current_operation = current_span.operation

            ScoutOtelHandler.otel_handler.emit(record)
        finally:
            self._handling_log.value = False

    def close(self):
        """
        We intentionally don't shutdown the LoggerProvider here because:
        1. We use a singleton pattern - the LoggerProvider is shared between instances.
        2. Django calls close() during configuration, not just on shutdown.

        The LoggerProvider manages its own lifecycle and will call shutdown() when the
        application exits.
        """
        super().close()

    # These getters will be replaced by a config module to read these values
    # from a config file or environment variables as the Scout APM agent does.

    def _get_service_name(self, provided_name):
        if provided_name:
            return provided_name

        # Try to get the name from Scout APM config
        scout_name = scout_config.value("name")
        if scout_name:
            return scout_name

        return "unnamed-service"

    def _get_endpoint(self):
        return (
            scout_config.value("logs_reporting_endpoint") or "otlp.scoutotel.com:4317"
        )

    def _get_ingest_key(self):
        ingest_key = scout_config.value("logs_ingest_key")
        if not ingest_key:
            raise ValueError("SCOUT_LOGS_INGEST_KEY is not set")
        return ingest_key
