import requests
from src import FB_ACCESS_TOKEN, FB_GROUP_ID, FB_API_VERSION

_GRAPH_BASE = 'https://graph.facebook.com'


def post_to_group(message: str, group_id: str = None) -> dict:
    gid = group_id or FB_GROUP_ID
    token = FB_ACCESS_TOKEN

    if not gid or not token:
        return {'success': False, 'error': '請先在 conf/config.ini 設定 FB_ACCESS_TOKEN 與 FB_GROUP_ID'}

    try:
        resp = requests.post(
            f'{_GRAPH_BASE}/{FB_API_VERSION}/{gid}/feed',
            data={'message': message, 'access_token': token},
            timeout=15,
        )
        data = resp.json()
    except requests.RequestException as e:
        return {'success': False, 'error': str(e)}

    if resp.ok and 'id' in data:
        return {'success': True, 'post_id': data['id']}

    err_msg = data.get('error', {}).get('message', '發文失敗，請確認 Token 與 Group ID')
    return {'success': False, 'error': err_msg}
