from datetime import datetime
from bson import ObjectId
from src.mongo import get_db
from src.models.base import BaseModel

ORDER_STATUSES = ['pending', 'processing', 'completed', 'cancelled']
STATUS_LABELS = {
    'pending':    '待處理',
    'processing': '處理中',
    'completed':  '已完成',
    'cancelled':  '已取消',
}


class Order(BaseModel):
    COLLECTION = 'orders'

    @classmethod
    def _col(cls):
        return get_db()[cls.COLLECTION]

    @classmethod
    def find_all(cls, status: str = None) -> list:
        q = {}
        if status:
            q['status'] = status
        return [cls._serialize(d) for d in cls._col().find(q).sort('created_at', -1)]

    @classmethod
    def find_by_id(cls, order_id: str) -> dict | None:
        try:
            return cls._serialize(cls._col().find_one({'_id': ObjectId(order_id)}))
        except Exception:
            return None

    @classmethod
    def create(cls, customer_name: str, customer_phone: str, items: list,
               total: float, note: str = '') -> str:
        doc = {
            'customer_name':  customer_name,
            'customer_phone': customer_phone,
            'items':  items,
            'total':  float(total),
            'note':   note,
            'status': 'pending',
            'created_at': datetime.now(),
        }
        return str(cls._col().insert_one(doc).inserted_id)

    @classmethod
    def update_status(cls, order_id: str, status: str) -> bool:
        if status not in ORDER_STATUSES:
            return False
        try:
            result = cls._col().update_one(
                {'_id': ObjectId(order_id)},
                {'$set': {'status': status}},
            )
            return result.matched_count > 0
        except Exception:
            return False
