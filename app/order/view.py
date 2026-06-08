from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.models.order import Order, ORDER_STATUSES
from src.models.product import Product
from src.permissions import require_role

app_order = Blueprint('order', __name__)


# ── 公開 API（顧客使用）────────────────────────────────────────────

@app_order.route('/public/products', methods=['GET'])
def public_products():
    """
    取得上架中產品（顧客下單用）
    ---
    tags: [Order-Public]
    responses:
      200:
        description: 成功
    """
    return jsonify({'success': True, 'data': Product.find_listed()})


@app_order.route('/public/', methods=['POST'])
def submit_order():
    """
    顧客提交訂單
    ---
    tags: [Order-Public]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [customer_name, customer_phone, items]
          properties:
            customer_name:  {type: string}
            customer_phone: {type: string}
            note:           {type: string}
            items:
              type: array
              items:
                type: object
                properties:
                  product_id:   {type: string}
                  product_name: {type: string}
                  price:        {type: number}
                  quantity:     {type: integer}
    responses:
      201:
        description: 訂單建立成功
    """
    data = request.get_json() or {}
    name  = data.get('customer_name', '').strip()
    phone = data.get('customer_phone', '').strip()
    note  = data.get('note', '').strip()
    items = data.get('items', [])

    if not name or not phone:
        return jsonify({'success': False, 'message': '姓名與電話不得為空'}), 400
    if len(name) > 50:
        return jsonify({'success': False, 'message': '姓名不得超過 50 字'}), 400
    if len(phone) > 20:
        return jsonify({'success': False, 'message': '電話不得超過 20 字'}), 400
    if len(note) > 500:
        return jsonify({'success': False, 'message': '備註不得超過 500 字'}), 400
    if not items:
        return jsonify({'success': False, 'message': '請至少選擇一項商品'}), 400
    if len(items) > 50:
        return jsonify({'success': False, 'message': '單筆訂單最多 50 種商品'}), 400

    # 合併相同 product_id 的數量，防止重複提交繞過庫存檢查
    qty_map: dict[str, int] = {}
    for i in items:
        pid = i.get('product_id', '')
        try:
            qty = int(i.get('quantity', 1))
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': '商品數量格式錯誤'}), 400
        if qty < 1 or qty > 9999:
            return jsonify({'success': False, 'message': '商品數量須介於 1 ~ 9999'}), 400
        qty_map[pid] = qty_map.get(pid, 0) + qty

    # 批次查詢，一次 round-trip 取得所有產品
    product_map = Product.find_by_ids(list(qty_map.keys()))

    validated_items = []
    for pid, qty in qty_map.items():
        if qty > 9999:
            return jsonify({'success': False, 'message': '商品數量須介於 1 ~ 9999'}), 400
        p = product_map.get(pid)
        if not p:
            return jsonify({'success': False, 'message': '商品不存在'}), 400
        if p['status'] != 'listed':
            return jsonify({'success': False, 'message': f'「{p["name"]}」已下架'}), 400
        if p['stock'] < qty:
            return jsonify({'success': False, 'message': f'「{p["name"]}」庫存不足（剩 {p["stock"]}）'}), 400
        validated_items.append({
            'product_id':   p['_id'],
            'product_name': p['name'],
            'price':        p['price'],
            'quantity':     qty,
        })

    total = round(sum(i['price'] * i['quantity'] for i in validated_items), 2)

    # 先原子扣減庫存再建單，避免 TOCTOU 超賣
    # 若任一商品扣減失敗，回滾已扣減的庫存並回報錯誤
    decremented = []
    for item in validated_items:
        if not Product.decrement_stock(item['product_id'], item['quantity']):
            for d in decremented:
                Product.restore_stock(d['product_id'], d['quantity'])
            p = product_map.get(item['product_id'])
            pname = p['name'] if p else '商品'
            return jsonify({'success': False, 'message': f'「{pname}」庫存不足，請重新確認'}), 409
        decremented.append(item)

    try:
        oid = Order.create(
            customer_name=name,
            customer_phone=phone,
            items=validated_items,
            total=total,
            note=note,
        )
    except Exception:
        for d in validated_items:
            Product.restore_stock(d['product_id'], d['quantity'])
        return jsonify({'success': False, 'message': '建立訂單失敗，請稍後再試'}), 500

    return jsonify({'success': True, 'id': oid}), 201


# ── 後台 API（需登入）─────────────────────────────────────────────

@app_order.route('/', methods=['GET'])
@jwt_required()
def list_orders():
    """
    列出訂單
    ---
    tags: [Order]
    security:
      - Bearer: []
    parameters:
      - in: query
        name: status
        type: string
        enum: [pending, processing, completed, cancelled]
    responses:
      200:
        description: 成功
    """
    status = request.args.get('status')
    return jsonify({'success': True, 'data': Order.find_all(status)})


@app_order.route('/<order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    """
    取得單一訂單
    ---
    tags: [Order]
    security:
      - Bearer: []
    """
    o = Order.find_by_id(order_id)
    if not o:
        return jsonify({'success': False, 'message': '找不到訂單'}), 404
    return jsonify({'success': True, 'data': o})


@app_order.route('/<order_id>/status', methods=['PATCH'])
@jwt_required()
@require_role('admin', 'operator')
def update_status(order_id):
    """
    更新訂單狀態
    ---
    tags: [Order]
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
            status:
              type: string
              enum: [pending, processing, completed, cancelled]
    responses:
      200:
        description: 更新成功
    """
    data = request.get_json() or {}
    status = data.get('status')
    if status not in ORDER_STATUSES:
        return jsonify({'success': False, 'message': f'status 須為 {ORDER_STATUSES}'}), 400
    if not Order.update_status(order_id, status):
        return jsonify({'success': False, 'message': '找不到訂單'}), 404
    return jsonify({'success': True})
