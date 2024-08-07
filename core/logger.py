import sys
import time
from pathlib import Path
from loguru import logger as Logger

basic_logger_format = "<level>{level}:     {message}</level>"
report_logger_format = "<green>[{time:YYYY-MM-DD HH:mm:ss}][REPORT]</green>: {message}"

class LoggingLogger:
    def __init__(self):
        self.log = Logger
        self.log.remove()
        self.log.add(sys.stderr, format=basic_logger_format, level="DEBUG", colorize=True)
        self.log.add(
            Path("./logs/{time:YYYY-MM-DD}.log"),
            retention="10 days",
            encoding="utf-8",
        )
        self.info = self.log.info
        self.debug = self.log.debug
        self.warning = self.log.warning
        self.error = self.log.error
        self.success = self.log.success

logger = LoggingLogger()