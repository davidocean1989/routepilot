"""Minimal JSON diagnostics without raw addresses, request bodies or credentials."""
import json
import logging
from contextvars import ContextVar

request_id = ContextVar('request_id', default=None)
logger = logging.getLogger('routepilot')


def configure_logging():
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)
    logger.propagate = False


def log(event, **fields):
    logger.info(json.dumps({'event': event, 'request_id': request_id.get(), **fields}, ensure_ascii=False))
