"""
Voice Studio 结构化日志配置
"""
import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor


def setup_logging(json_format: bool = False, log_level: str = "INFO") -> None:
    """
    配置结构化日志

    Args:
        json_format: 是否使用 JSON 格式输出（生产环境推荐）
        log_level: 日志级别
    """
    # 共享的处理器
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_format:
        # JSON 格式（生产环境）
        shared_processors.append(structlog.processors.format_exc_info)
        renderer = structlog.processors.JSONRenderer()
    else:
        # 控制台彩色输出（开发环境）
        shared_processors.append(structlog.dev.set_exc_info)
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    # 配置 structlog
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # 配置标准库 logging
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # 设置根 logger
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # 降低第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("multipart").setLevel(logging.WARNING)


def get_logger(name: str = "voice_studio") -> structlog.stdlib.BoundLogger:
    """
    获取 logger 实例

    Args:
        name: logger 名称

    Returns:
        structlog BoundLogger 实例
    """
    return structlog.get_logger(name)


def bind_request_context(**kwargs: Any) -> None:
    """
    绑定请求上下文到日志

    Args:
        **kwargs: 要绑定的上下文变量
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_request_context() -> None:
    """清除请求上下文"""
    structlog.contextvars.unbind_contextvars(*list(structlog.contextvars.get_contextvars().keys()))