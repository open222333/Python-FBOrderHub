import requests
from src import FB_ACCESS_TOKEN, FB_GROUP_ID, FB_API_VERSION

_GRAPH_BASE = 'https://graph.facebook.com'


def post_to_group(message: str, group_id: str = None) -> dict:
    gid = group_id or FB_GROUP_ID

    if not gid or not FB_ACCESS_TOKEN:
        return {'success': False, 'error': '請先在 conf/config.ini 設定 FB_ACCESS_TOKEN 與 FB_GROUP_ID'}

    # 社團 ID 必須為純數字，防止路徑穿越攻擊
    if not str(gid).isdigit():
        return {'success': False, 'error': '無效的 FB Group ID'}

    try:
        resp = requests.post(
            f'{_GRAPH_BASE}/{FB_API_VERSION}/{gid}/feed',
            data={'message': message, 'access_token': FB_ACCESS_TOKEN},
            timeout=15,
        )
        data = resp.json()
    except requests.RequestException:
        return {'success': False, 'error': 'Facebook API 請求失敗，請稍後再試'}

    if resp.ok and 'id' in data:
        return {'success': True, 'post_id': data['id']}

    err_msg = data.get('error', {}).get('message', '發文失敗，請確認 Token 與 Group ID')
    return {'success': False, 'error': err_msg}
