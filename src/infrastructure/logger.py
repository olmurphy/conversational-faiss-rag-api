import logging
import os
import socket
import sys
import time
import uuid

import psutil
from api.middlewares.contextvars import request_id_var
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def process_log_record(self, log_record):
        # Time and Level
        log_record["severity"] = logging.getLevelName(int(log_record.pop("levelno")))
        log_record["timestamp"] = (
            time.strftime("%Y-%m-%dT%H:%M:%S.", time.gmtime(time.time()))
            + str(int((time.time() * 1000) % 1000)).zfill(3)
            + "Z"
        )

        # Process Information
        log_record["pid"] = os.getpid()
        log_record["service"] = os.environ.get("SERVICE_NAME", "KrogerMX-gen-ai")
        log_record["host"] = socket.gethostname()

        # Tracing Information (grouped)
        log_record["request_id"] = request_id_var.get(None)
        log_record["transaction_id"] = log_record.pop(
            "transaction_id", str(uuid.uuid4())
        )
        log_record["span_id"] = log_record.pop("span_id", str(uuid.uuid4()))
        log_record["session_id"] = log_record.pop("session_id", "unknown")
        log_record["user_id"] = log_record.pop("user_id", "unknown")
        log_record["user_role"] = log_record.pop("user_role", "unknown")

        # Request/Response Data
        log_record["request_payload_size"] = self._count_string_bytes(
            log_record.get("request_payload_size", None)
        )
        log_record["response_payload_size"] = self._count_string_bytes(
            log_record.get("response_payload_size", None)
        )

        # Event and Message (Message last)
        log_record["event"] = log_record.get("event", "unknown")

        # Location Information
        location_info = {
            "filename": log_record.pop("filename", None),
            "pathname": log_record.pop("pathname", None),
            "line": log_record.pop("lineno", "unknown"),
            "funcName": log_record.pop("funcName", None),
            "module": log_record.pop("module", None),
            "stack_info": log_record.pop("stack_info", None),
            "taskName": log_record.pop("taskName", None),
            "processName": log_record.pop("processName", None),
        }
        log_record["location_info"] = location_info

        # Extra Data and Error
        log_record["data"] = log_record.get("data", None)
        log_record["error"] = log_record.get("error", None)

        log_record["message"] = log_record.pop("message")

        # Resource Utilization
        log_record["resource_utilization"] = {
            "cpu_percent": f"{psutil.cpu_percent():.2f}%",
            "memory_percent": f"{psutil.virtual_memory().percent:.2f}%",
            "disk_read_bytes": self._count_string_bytes(
                psutil.disk_io_counters().read_bytes
            ),
            "disk_write_bytes": self._count_string_bytes(
                psutil.disk_io_counters().write_bytes
            ),
            "network_bytes_sent": self._count_string_bytes(
                psutil.net_io_counters().bytes_sent
            ),
            "network_bytes_received": self._count_string_bytes(
                psutil.net_io_counters().bytes_recv
            ),
        }

        return super().process_log_record(log_record)

    def _count_string_bytes(self, value):
        """Helper function to count bytes in a string."""
        if isinstance(value, (str, int)):
            byte_count = len(str(value).encode("utf-8"))
            return self._format_bytes(byte_count)  # Count bytes using UTF-8 encoding
        else:
            return None

    def _format_bytes(self, size):
        """Formats bytes into a human-readable string (B, KB, MB, GB, TB, etc.)."""
        power = 2**10
        n = 0
        power_labels = {
            0: "B",
            1: "KB",
            2: "MB",
            3: "GB",
            4: "TB",
            5: "PB",
            6: "EB",
            7: "ZB",
            8: "YB",
        }
        while size > power:
            size /= power
            n += 1
        return f"{size:.2f} {power_labels.get(n, 'Unknown')}"


def get_logger(logger_name="mialogger") -> logging.Logger:
    # Clear any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logger = logging.getLogger(logger_name)
    log_level = os.environ.get("LOG_LEVEL", logging.INFO)
    logging.root.setLevel(log_level)
    logger.setLevel(log_level)

    formatter = CustomJsonFormatter(
        fmt="%(asctime)s %(created)f %(pid)s %(levelno)s %(message)s %(filename)s %(lineno)s %(module)s %(funcName)s %(pathname)s %(processName)s %(stack_info)s %(taskName)s",
    )

    # Create a new handler with a filterd
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(lambda record: record.name.startswith(logger_name))
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False

    log_level = logging.getLevelName(logger.getEffectiveLevel())

    logger.info({"message": f"Application starting with log level: {log_level}"})

    return logger
