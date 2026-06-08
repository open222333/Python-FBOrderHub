from datetime import datetime
from bson import ObjectId
from src.mongo import get_db
from src.models.base import BaseModel


class Product(BaseModel):
    COLLECTION = 'products'

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
    def find_listed(cls) -> list:
        """顧客下單用：回傳上架清單（排程器負責自動下架，不在此重複寫入）"""
        return [cls._serialize(d) for d in cls._col().find({'status': 'listed'}).sort('created_at', -1)]

    @classmethod
    def find_by_id(cls, product_id: str) -> dict | None:
        try:
            return cls._serialize(cls._col().find_one({'_id': ObjectId(product_id)}))
        except Exception:
            return None

    @classmethod
    def create(cls, name: str, description: str = '', price: float = 0,
               stock: int = 0, images: list = None, status: str = 'unlisted',
               scheduled_unpublish_at: datetime = None) -> str:
        now = datetime.now()
        doc = {
            'name': name,
            'description': description,
            'price': float(price),
            'stock': int(stock),
            'images': images or [],
            'status': status,
            'scheduled_unpublish_at': scheduled_unpublish_at,
            'created_at': now,
            'updated_at': now,
        }
        return str(cls._col().insert_one(doc).inserted_id)

    @classmethod
    def update(cls, product_id: str, **kwargs) -> bool:
        set_fields = {'updated_at': datetime.now()}
        unset_fields = {}
        for k, v in kwargs.items():
            if v is None and k == 'scheduled_unpublish_at':
                unset_fields[k] = ''
            else:
                set_fields[k] = v
        op = {'$set': set_fields}
        if unset_fields:
            op['$unset'] = unset_fields
        try:
            result = cls._col().update_one({'_id': ObjectId(product_id)}, op)
            return result.matched_count > 0
        except Exception:
            return False

    @classmethod
    def delete(cls, product_id: str) -> bool:
        try:
            return cls._col().delete_one({'_id': ObjectId(product_id)}).deleted_count > 0
        except Exception:
            return False

    @classmethod
    def find_by_ids(cls, product_ids: list) -> dict:
        """批次查詢，回傳 {str_id: serialized_doc}"""
        if not product_ids:
            return {}
        try:
            oids = [ObjectId(pid) for pid in product_ids]
        except Exception:
            return {}
        return {str(d['_id']): cls._serialize(d) for d in cls._col().find({'_id': {'$in': oids}})}

    @classmethod
    def decrement_stock(cls, product_id: str, qty: int) -> bool:
        """原子扣減庫存；庫存不足時不執行並回傳 False"""
        try:
            result = cls._col().update_one(
                {'_id': ObjectId(product_id), 'stock': {'$gte': qty}},
                {'$inc': {'stock': -qty}, '$set': {'updated_at': datetime.now()}},
            )
            return result.modified_count > 0
        except Exception:
            return False

    @classmethod
    def restore_stock(cls, product_id: str, qty: int) -> bool:
        """回滾庫存（訂單建立失敗時呼叫）"""
        try:
            result = cls._col().update_one(
                {'_id': ObjectId(product_id)},
                {'$inc': {'stock': qty}, '$set': {'updated_at': datetime.now()}},
            )
            return result.modified_count > 0
        except Exception:
            return False

    @classmethod
    def auto_unpublish(cls):
        """將已超過排程時間的上架產品自動下架"""
        now = datetime.now()
        cls._col().update_many(
            {'status': 'listed', 'scheduled_unpublish_at': {'$lte': now, '$ne': None}},
            {'$set': {'status': 'unlisted', 'updated_at': now}},
        )
