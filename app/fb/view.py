from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.models.fb_template import FBTemplate
from src.fb_client import post_to_group
from src.permissions import require_role

app_fb = Blueprint('fb', __name__)


@app_fb.route('/templates/', methods=['GET'])
@jwt_required()
def list_templates():
    """
    列出 FB 發文模板
    ---
    tags: [FB]
    security:
      - Bearer: []
    responses:
      200:
        description: 成功
    """
    return jsonify({'success': True, 'data': FBTemplate.find_all()})


@app_fb.route('/templates/', methods=['POST'])
@jwt_required()
@require_role('admin', 'operator')
def create_template():
    """
    新增 FB 發文模板
    ---
    tags: [FB]
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [name, content]
          properties:
            name:    {type: string}
            content: {type: string, description: "可用占位符：{name} {price} {description} {stock}"}
    responses:
      201:
        description: 新增成功
    """
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    content = data.get('content', '').strip()
    if not name or not content:
        return jsonify({'success': False, 'message': 'name 與 content 不得為空'}), 400
    tid = FBTemplate.create(name, content)
    return jsonify({'success': True, 'id': tid}), 201


@app_fb.route('/templates/<tid>', methods=['PUT'])
@jwt_required()
@require_role('admin', 'operator')
def update_template(tid):
    """
    更新 FB 發文模板
    ---
    tags: [FB]
    security:
      - Bearer: []
    """
    data = request.get_json() or {}
    if not FBTemplate.update(tid, data.get('name'), data.get('content')):
        return jsonify({'success': False, 'message': '找不到模板'}), 404
    return jsonify({'success': True})


@app_fb.route('/templates/<tid>', methods=['DELETE'])
@jwt_required()
@require_role('admin')
def delete_template(tid):
    """
    刪除 FB 發文模板
    ---
    tags: [FB]
    security:
      - Bearer: []
    """
    if not FBTemplate.delete(tid):
        return jsonify({'success': False, 'message': '找不到模板'}), 404
    return jsonify({'success': True})


@app_fb.route('/post', methods=['POST'])
@jwt_required()
@require_role('admin', 'operator')
def post():
    """
    發文至 Facebook 社團
    ---
    tags: [FB]
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [message]
          properties:
            message:  {type: string, description: "發文內容"}
            group_id: {type: string, description: "覆蓋預設社團 ID（選填）"}
    responses:
      200:
        description: 發文成功
      400:
        description: 發文失敗
    """
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'success': False, 'message': '發文內容不得為空'}), 400

    result = post_to_group(message, data.get('group_id'))
    status = 200 if result['success'] else 400
    return jsonify(result), status
