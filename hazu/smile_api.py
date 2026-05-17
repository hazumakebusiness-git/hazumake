import hashlib
import json
import logging
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings

logger = logging.getLogger(__name__)


def make_sign(params):
    # Sort by key → "key=value&" joined → append KEY → md5(md5())
    s = "".join(f"{k}={v}&" for k, v in sorted(params.items()))
    s += settings.SMILE_KEY
    return hashlib.md5(
        hashlib.md5(s.encode('utf-8')).hexdigest().encode('utf-8')
    ).hexdigest()


def smile_post(endpoint, extra_params):
    params = {
        'uid': settings.SMILE_UID,
        'email': settings.SMILE_EMAIL,
        'time': int(time.time()),
        **extra_params,
    }
    params['sign'] = make_sign(params)
    url = f"{settings.SMILE_BASE_URL}/{endpoint}"
    encoded = urlencode(params).encode('utf-8')
    request = Request(url, data=encoded)
    request.add_header('Content-Type', 'application/x-www-form-urlencoded')
    with urlopen(request, timeout=30) as response:
        payload = response.read().decode('utf-8')
    return json.loads(payload)


def get_product_list(game_slug):
    response = smile_post('productlist', {'product': game_slug})
    return response.get('data', {}).get('product', [])


def verify_player(game_slug, player_uid, player_sid=''):
    extra = {
        'product': game_slug,
        'uid': player_uid,
    }
    if player_sid:
        extra['sid'] = player_sid
    try:
        response = smile_post('getuserinfo', extra)
        print("VERIFY RESPONSE:", response)
        if response.get('status') == 200:
            data = response.get('data', {})
            return data.get('username') or data.get('name') or data.get('nickname')
        return None
    except Exception as e:
        print("VERIFY ERROR:", e)
        return None


def create_order(game_slug, product_id, player_uid, player_sid=''):
    """
    Place an order on Smile.one.
    Returns the smile order ID string on success, None on failure.
    """
    extra = {
        'product': game_slug,
        'productid': str(product_id),
        'uid': player_uid,
    }
    if player_sid:
        extra['sid'] = player_sid

    try:
        response = smile_post('createorder', extra)
        print("SMILE RESPONSE:", response)
        logger.info("Smile.one create_order response: %s", response)
        if response.get('status') == 200:
            return str(response.get('order_id') or response.get('game_order', ''))
        else:
            logger.error("Smile.one order failed: %s", response)
            return None
    except Exception as e:
        print("SMILE ERROR:", e)
        logger.error("Smile.one create_order exception: %s", e)
        return None