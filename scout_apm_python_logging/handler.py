import logging
import os
import threading
import enum
from opentelemetry import _logs
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from scout_apm.core.tracked_request import TrackedRequest
from scout_apm.core import scout_config


class OtelScoutHandler(logging.Handler):
    def __init__(self, service_name):
        super().__init__()
        self.service_name = service_name
        self.logger_provider = None
        self.ingest_key = self._get_ingest_key()
        self.endpoint = self._get_endpoint()
        self.setup_logging()
        self._handling_log = threading.local()

    def setup_logging(self):
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
            headers={"x-telemetryhub-key": self.ingest_key},
            endpoint=self.endpoint,
        )
        self.logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(otlp_exporter)
        )

        self.otel_handler = LoggingHandler(
            level=logging.NOTSET, logger_provider=self.logger_provider
        )

    def emit(self, record):
        if self.should_ignore_log(record):
            return

        if getattr(self._handling_log, "value", False):
            # We're already handling a log message, so don't try to get the TrackedRequest
            return self.otel_handler.emit(record)

        try:
            self._handling_log.value = True
            scout_request = TrackedRequest.instance()

            if scout_request:
                # Add Scout-specific attributes to the log record
                record.scout_request_id = scout_request.request_id
                record.scout_start_time = scout_request.start_time.isoformat()
                if scout_request.end_time:
                    record.scout_end_time = scout_request.end_time.isoformat()

                # Add duration if the request is completed
                if scout_request.end_time:
                    record.scout_duration = (
                        scout_request.end_time - scout_request.start_time
                    ).total_seconds()

                # Add tags
                for key, value in scout_request.tags.items():
                    setattr(record, f"scout_tag_{key}", value)

                # Add the current span's operation if available
                current_span = scout_request.current_span()
                if current_span:
                    record.scout_current_operation = current_span.operation

            # Handle Enum values in the log record
            self.handle_enums(record)

            self.otel_handler.emit(record)
        except Exception as e:
            print(f"Error in OtelScoutHandler.emit: {e}")
        finally:
            self._handling_log.value = False

    def handle_enums(self, record):
        if isinstance(record.msg, enum.EnumMeta):
            print("found an enum class")
            for attr, value in record.__dict__.items():
                print(f"attr: {attr}, value: {value} type {type(value)}")
            record.msg = f"Enum class: {record.msg.__name__}"
        elif isinstance(record.msg, enum.Enum):
            record.msg = f"{record.msg.__class__.__name__}.{record.msg.name}"

        for attr, value in record.__dict__.items():
            if isinstance(value, enum.EnumMeta):
                setattr(record, attr, f"Enum class: {value.__name__}")
            elif isinstance(value, enum.Enum):
                setattr(record, attr, f"{value.__class__.__name__}.{value.name}")

    def should_ignore_log(self, record):
        # Ignore logs from the OpenTelemetry exporter
        if record.name.startswith("opentelemetry.exporter.otlp"):
            return True

        return False

    def close(self):
        if self.logger_provider:
            self.logger_provider.shutdown()
        super().close()

    def _get_service_name(self, provided_name):
        if provided_name:
            return provided_name

        # Try to get the name from Scout APM config
        scout_name = scout_config.value("name")
        if scout_name:
            return scout_name

        # Fallback to a default name if neither is available
        return "unnamed-service"

    # These getters will be replaced by a config module to read these values
    # from a config file or environment variables as the Scout APM agent does.

    def _get_endpoint(self):
        return os.getenv("SCOUT_LOGS_REPORTING_ENDPOINT", "otlp.scoutotel.com:4317")

    def _get_ingest_key(self):
        ingest_key = os.getenv("SCOUT_LOGS_INGEST_KEY")
        if not ingest_key:
            raise ValueError("SCOUT_LOGS_INGEST_KEY is not set")
        return ingest_key
