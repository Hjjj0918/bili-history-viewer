from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging() -> None:
    """初始化本地日志文件（按大小轮转）。"""
    log_dir = Path.cwd() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "bili_viewer.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 避免重复添加 handler（例如某些调试场景下重复初始化）。
    for handler in root_logger.handlers:
        if isinstance(handler, RotatingFileHandler) and Path(handler.baseFilename) == log_file:
            return

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
