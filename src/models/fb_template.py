from datetime import datetime
from bson import ObjectId
from src.mongo import get_db
from src.models.base import BaseModel


class FBTemplate(BaseModel):
    COLLECTION = 'fb_templates'

    @classmethod
    def _col(cls):
        return get_db()[cls.COLLECTION]

    @classmethod
    def find_all(cls) -> list:
        return [cls._serialize(d) for d in cls._col().find({}).sort('created_at', -1)]

    @classmethod
    def find_by_id(cls, tid: str) -> dict | None:
        try:
            return cls._serialize(cls._col().find_one({'_id': ObjectId(tid)}))
        except Exception:
            return None

    @classmethod
    def create(cls, name: str, content: str) -> str:
        now = datetime.now()
        return str(cls._col().insert_one({'name': name, 'content': content, 'created_at': now}).inserted_id)

    @classmethod
    def update(cls, tid: str, name: str = None, content: str = None) -> bool:
        fields = {}
        if name is not None:
            fields['name'] = name
        if content is not None:
            fields['content'] = content
        if not fields:
            return False
        try:
            result = cls._col().update_one({'_id': ObjectId(tid)}, {'$set': fields})
            return result.matched_count > 0
        except Exception:
            return False

    @classmethod
    def delete(cls, tid: str) -> bool:
        try:
            return cls._col().delete_one({'_id': ObjectId(tid)}).deleted_count > 0
        except Exception:
            return False
