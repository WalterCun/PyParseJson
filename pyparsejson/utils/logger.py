# pyparsejson/utils/logger.py
import logging
from typing import Optional


class RepairLogger:
    def __init__(self, name: str = "pyparsejson", level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '[%(levelname)s] %(name)s: %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def debug_tokens(self, stage: str, tokens: list):
        """Log tokens en formato legible"""
        token_str = " ".join(f"{t.type.name}:{t.value}" for t in tokens[:10])
        self.logger.debug(f"{stage} ({len(tokens)} tokens): {token_str}...")

    def info(self, msg: str):
        self.logger.info(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def error(self, msg: str):
        self.logger.error(msg)