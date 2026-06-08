from datetime import datetime


class BaseModel:

    @classmethod
    def _serialize(cls, doc) -> dict | None:
        if not doc:
            return None
        d = {'_id': str(doc['_id'])}
        for k, v in doc.items():
            if k == '_id':
                continue
            if isinstance(v, datetime):
                d[k] = v.isoformat()
            else:
                d[k] = v
        return d
