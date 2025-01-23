# Scout APM Python Logging Agent

A Python package for detailed, easy-to-navigate, managed log monitoring. Sign up for an account at https://www.scoutapm.com to start monitoring your logs and application performance in minutes.

This is to be used alongside [scout-apm-python](https://github.com/scoutapp/scout_apm_python) package, thusly requires it. 

To use Scout, you'll need to
[sign up for an account](https://scoutapm.com/users/sign_up) or use
[our Heroku Addon](https://devcenter.heroku.com/articles/scout).

Then, you'll need to enable logging for your individual apps, which will provide a `SCOUT_LOGS_INGEST_KEY`

## Installation

Install the Scout APM Python Logging Agent using pip:

```
pip install scout-apm-python-logging
```

## Setup and Usage

### Using dictConfig

We recommend setting up the `ScoutOtelHandler` using Python's [`dictConfig`](https://docs.python.org/3/library/logging.config.html#logging.config.dictConfig). Here's an example configuration:

```python
import logging
from logging.config import dictConfig
from scout_apm_logging import ScoutOtelHandler

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
    },
    "handlers": {
        "otel": {
            "level": "DEBUG",
            "class": "scout_apm_logging.ScoutOtelHandler",
            "service_name": "your-service-name",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "loggers": {
        "": {  # Root logger
            "handlers": ["console", "otel"],
            "level": "DEBUG",
        },
    },
}

# Apply the logging configuration
dictConfig(LOGGING_CONFIG)
```

### Adding to an Existing Logger

You can also add the `ScoutOtelHandler` to an existing logger:

```python
import logging
from scout_apm_logging import ScoutOtelHandler

# Get your logger
logger = logging.getLogger(__name__)

# Create and add the ScoutOtelHandler
handler = ScoutOtelHandler(service_name="your-service-name")
logger.addHandler(handler)
```

> Alternative logging configurations are covered in our [documentation](/https://scoutapm.com/docs/features/log-management#common-configurations-python)

## Configuration

The `ScoutOtelHandler` only requires `service_name` to be supplied to the handler as an argument:

If the `scout-apm` is [configured](https://scoutapm.com/docs/python#some-configuration-required) (You've set your `SCOUT_KEY`, etc), you'll only need add your `SCOUT_LOGS_INGEST_KEY` to whichever configuration you are already using. This can also be set as an environment variable.

Make sure to set the `SCOUT_LOGS_INGEST_KEY` variable in the above configuration before running your application.

## OpenTelemetry

The Scout APM Python Logging Agent leverages [OpenTelemetry Python](https://github.com/open-telemetry/opentelemetry-python) to provide powerful and standardized logging capabilities. OpenTelemetry is an observability framework for cloud-native software, offering a collection of tools, APIs, and SDKs for generating, collecting, and exporting telemetry data (metrics, logs, and traces).

Our `ScoutOtelHandler` utilizes the OpenTelemetry Python SDK to:

1. Create a `LoggerProvider` with a custom resource that includes your service name and instance ID.
2. Set up an OTLP (OpenTelemetry Protocol) exporter configured to send logs to Scout's ingestion endpoint.
3. Add a `BatchLogRecordProcessor` to efficiently process and export log records.
4. Integrate with Scout APM's request tracking to enrich logs with request-specific information.

This integration allows you to benefit from OpenTelemetry's standardized approach to observability while leveraging Scout APM's powerful analysis and visualization tools.

For more information about OpenTelemetry and its Python SDK, visit the [OpenTelemetry Python documentation](https://opentelemetry.io/docs/instrumentation/python/).

## Additional Resources

For more information on using Scout APM and advanced configuration options, please refer to our [documentation](https://docs.scoutapm.com).

## Support

If you encounter any issues or have questions, please [open an issue](https://github.com/scoutapp/scout-apm-python-logging/issues) on our GitHub repository or contact our support team at support@scoutapm.com.
