import threading
import logging

logger = logging.getLogger(__name__)

_timer: threading.Timer | None = None


def _tick():
    global _timer
    try:
        from src.models.product import Product
        Product.auto_unpublish()
    except Exception as e:
        logger.warning('scheduler auto_unpublish error: %s', e)
    _timer = threading.Timer(60, _tick)
    _timer.daemon = True
    _timer.start()


def start():
    global _timer
    if _timer is not None:
        return
    _timer = threading.Timer(60, _tick)
    _timer.daemon = True
    _timer.start()
    logger.info('排程器已啟動（每分鐘檢查自動下架）')


def stop():
    global _timer
    if _timer:
        _timer.cancel()
        _timer = None
