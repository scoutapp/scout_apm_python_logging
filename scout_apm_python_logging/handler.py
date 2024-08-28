import logging
import os
from opentelemetry import _logs
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource


class OtelScoutHandler(logging.Handler):
    def __init__(self, service_name):
        super().__init__()
        self.service_name = service_name
        self.logger_provider = None
        self.ingest_key = self._get_ingest_key()
        self.endpoint = self._get_endpoint()
        self.setup_logging()

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
        print("Emitting log")
        self.otel_handler.emit(record)

    def close(self):
        if self.logger_provider:
            self.logger_provider.shutdown()
        super().close()

    # These getters will be replaced by a config module to read these values
    # from a config file or environment variables as the Scout APM agent does.
    def _get_endpoint(self):
        return os.getenv(
            "SCOUT_LOGS_REPORTING_ENDPOINT", "otlp.scoutotel.com:4317"
        )

    def _get_ingest_key(self):
        ingest_key = os.getenv("SCOUT_LOGS_INGEST_KEY")
        if not ingest_key:
            raise ValueError("SCOUT_LOGS_INGEST_KEY is not set")
        return ingest_key