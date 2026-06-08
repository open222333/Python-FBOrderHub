from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.models.product import Product
from src.permissions import require_role

app_product = Blueprint('product', __name__)


VALID_STATUSES = ('listed', 'unlisted')


def _parse_dt(value: str) -> datetime | None | bool:
    """回傳 datetime（成功）/ None（空值，清除欄位）/ False（格式錯誤）"""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', ''))
    except ValueError:
        return False


@app_product.route('/', methods=['GET'])
@jwt_required()
def list_products():
    """
    列出產品
    ---
    tags: [Product]
    security:
      - Bearer: []
    parameters:
      - in: query
        name: status
        type: string
        enum: [listed, unlisted]
    responses:
      200:
        description: 成功
    """
    status = request.args.get('status')
    return jsonify({'success': True, 'data': Product.find_all(status)})


@app_product.route('/', methods=['POST'])
@jwt_required()
@require_role('admin', 'operator')
def create_product():
    """
    新增產品
    ---
    tags: [Product]
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [name]
          properties:
            name:                   {type: string}
            description:            {type: string}
            price:                  {type: number}
            stock:                  {type: integer}
            images:                 {type: array, items: {type: string}}
            status:                 {type: string, enum: [listed, unlisted]}
            scheduled_unpublish_at: {type: string, description: "ISO 8601 datetime"}
    responses:
      201:
        description: 新增成功
    """
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'success': False, 'message': '產品名稱不得為空'}), 400

    status = data.get('status', 'unlisted')
    if status not in VALID_STATUSES:
        return jsonify({'success': False, 'message': 'status 須為 listed 或 unlisted'}), 400

    scheduled = _parse_dt(data.get('scheduled_unpublish_at', ''))
    if scheduled is False:
        return jsonify({'success': False, 'message': '排程時間格式錯誤，請使用 ISO 8601'}), 400

    pid = Product.create(
        name=name,
        description=data.get('description', ''),
        price=float(data.get('price', 0)),
        stock=int(data.get('stock', 0)),
        images=data.get('images', []),
        status=status,
        scheduled_unpublish_at=scheduled,
    )
    return jsonify({'success': True, 'id': pid}), 201


@app_product.route('/<product_id>', methods=['GET'])
@jwt_required()
def get_product(product_id):
    """
    取得單一產品
    ---
    tags: [Product]
    security:
      - Bearer: []
    parameters:
      - in: path
        name: product_id
        required: true
        type: string
    responses:
      200:
        description: 成功
      404:
        description: 找不到
    """
    p = Product.find_by_id(product_id)
    if not p:
        return jsonify({'success': False, 'message': '找不到產品'}), 404
    return jsonify({'success': True, 'data': p})


@app_product.route('/<product_id>', methods=['PUT'])
@jwt_required()
@require_role('admin', 'operator')
def update_product(product_id):
    """
    更新產品資訊
    ---
    tags: [Product]
    security:
      - Bearer: []
    """
    data = request.get_json() or {}
    kwargs = {}

    if 'status' in data and data['status'] not in VALID_STATUSES:
        return jsonify({'success': False, 'message': 'status 須為 listed 或 unlisted'}), 400

    for field in ('name', 'description', 'price', 'stock', 'images', 'status'):
        if field in data:
            kwargs[field] = data[field]

    if 'scheduled_unpublish_at' in data:
        parsed = _parse_dt(data['scheduled_unpublish_at'])
        if parsed is False:
            return jsonify({'success': False, 'message': '排程時間格式錯誤'}), 400
        kwargs['scheduled_unpublish_at'] = parsed   # None = 清除

    if not kwargs:
        return jsonify({'success': False, 'message': '無更新內容'}), 400

    if not Product.update(product_id, **kwargs):
        return jsonify({'success': False, 'message': '找不到產品'}), 404
    return jsonify({'success': True})


@app_product.route('/<product_id>', methods=['DELETE'])
@jwt_required()
@require_role('admin')
def delete_product(product_id):
    """
    刪除產品
    ---
    tags: [Product]
    security:
      - Bearer: []
    """
    if not Product.delete(product_id):
        return jsonify({'success': False, 'message': '找不到產品'}), 404
    return jsonify({'success': True})


@app_product.route('/<product_id>/status', methods=['PATCH'])
@jwt_required()
@require_role('admin', 'operator')
def set_status(product_id):
    """
    切換產品上下架
    ---
    tags: [Product]
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [status]
          properties:
            status: {type: string, enum: [listed, unlisted]}
    """
    data = request.get_json() or {}
    status = data.get('status')
    if status not in VALID_STATUSES:
        return jsonify({'success': False, 'message': 'status 須為 listed 或 unlisted'}), 400
    if not Product.update(product_id, status=status):
        return jsonify({'success': False, 'message': '找不到產品'}), 404
    return jsonify({'success': True})
