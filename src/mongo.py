import threading
from pymongo import MongoClient
from src import MONGO_URI, MONGO_DB


_client = None
_db = None
_lock = threading.Lock()


def get_db():
    global _client, _db
    if _db is None:
        with _lock:
            if _db is None:
                _client = MongoClient(MONGO_URI)
                _db = _client[MONGO_DB]
    return _db
