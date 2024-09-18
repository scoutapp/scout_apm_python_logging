import logging

from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource


class OTELLoggingManager:
    def __init__(self, service_name):
        self.service_name = service_name
        self.logger_provider = None
        self.logs_reporting_endpoint = "https://otlp.scoutotel.com:4317"

        # placeholder, we will want to get this from a config or env var.
        self.ingest_key = "aaaa-bbbb-cccc-dddd"

    def setup_logging(self):
        self.logger_provider = LoggerProvider(
            resource=Resource.create({"service.name": self.service_name})
        )
        set_logger_provider(self.logger_provider)

        otlp_exporter = OTLPLogExporter(
            headers={"x-telemetryhub-key": self.ingest_key},
            endpoint=self.logs_reporting_endpoint,
        )

        self.logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(otlp_exporter)
        )

        handler = LoggingHandler(
            level=logging.NOTSET, logger_provider=self.logger_provider
        )
        # add otel logging handler to root logger
        logging.getLogger().addHandler(handler)

    def shutdown(self):
        if self.logger_provider:
            self.logger_provider.shutdown()


def initialize_otel_logging(service_name):
    manager = OTELLoggingManager(service_name)
    manager.setup_logging()
    return manager
