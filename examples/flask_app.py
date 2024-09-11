import os
from flask import Flask
import logging
from logging.config import dictConfig
from scout_apm.flask import ScoutApm

# Logging configuration
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
        "": {  # Root logger
            "handlers": ["console", "otel"],
            "level": "DEBUG",
        },
    },
}

# Apply the logging configuration
dictConfig(LOGGING_CONFIG)

# Create Flask app
app = Flask(__name__)

# Scout APM configuration
app.config["SCOUT_NAME"] = "Example Python App"
app.config["SCOUT_KEY"] = os.environ.get(
    "SCOUT_KEY"
)  # Make sure to set this environment variable

# Initialize Scout APM
ScoutApm(app)

# Get a logger
logger = logging.getLogger(__name__)


@app.route("/")
def hello():
    logger.info("Received request for hello endpoint")
    return "Hello, World!"


@app.route("/error")
def error():
    logger.error("This is a test error")
    return "Error logged", 500


@app.route("/debug")
def debug():
    logger.debug("This is a debug message")
    return "Debug message logged", 200


if __name__ == "__main__":
    logger.info("Starting Flask application")
    app.run(debug=True)
