import logging
from typing import Literal

from loguru import logger

from app.settings import LOG_FILE_ROTATION, LOG_LEVEL

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)


class InterceptHandler(logging.Handler):
    def emit(self, record):

        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_back and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO)


logger.add(
    "app.log",
    rotation=LOG_FILE_ROTATION,
    compression="zip",
    level=LOG_LEVEL,
    backtrace=True,
    diagnose=True,
)


loggers = (
    "uvicorn",
    "uvicorn.access",
    "uvicorn.error",
    "fastapi",
    "asyncio",
    "starlette",
)

for logger_name in loggers:
    logging_logger = logging.getLogger(logger_name)
    logging_logger.handlers = []
    logging_logger.propagate = True


def log_operation(
    operation: Literal["CREATE", "READ", "UPDATE", "DELETE"],
    model: str,
    tenant_id: int,
    status: Literal["SUCCESS", "FAILED", "PENDING"],
    user_id: int = None,
    detail: str | None = None,
    level: Literal["info", "warning", "error"] = "info",
):
    """Records a log operation in the application log."""
    user_part = f" by user {user_id}" if user_id else ""
    detail_part = f": {detail}" if detail else ""
    message = (
        f"{operation} {model} for tenant {tenant_id}{user_part} {status}{detail_part}"
    )

    match level:
        case "info":
            logger.info(message)
        case "warning":
            logger.warning(message)
        case "error":
            logger.error(message)
