# An example of how to use the scout handler with dictConfig,
# useful for early testing

import logging
import logging.config

# Example dictConfig
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"  # noqa E501
        },
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "otel": {
            "level": "DEBUG",
            "class": "scout_apm_python_logging.OtelScoutHandler",
            "service_name": "example-python-app",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "root": {
            "handlers": ["console", "otel"],
            "level": "DEBUG",
        },
    },
}

# Setup Logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


def log_some_stuff():
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")


if __name__ == "__main__":
    log_some_stuff()
