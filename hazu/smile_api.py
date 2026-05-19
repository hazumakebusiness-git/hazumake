import hashlib
import json
import logging
import time
from json import JSONDecodeError
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings

logger = logging.getLogger(__name__)


def make_sign(params):
    # Sort by key → "key=value" concatenated with no separator → append secret → md5
    clean_params = {k: v for k, v in params.items() if k != 'sign'}
    sign_string = ''.join(f"{k}={v}" for k, v in sorted(clean_params.items()))
    sign_string += settings.SMILE_KEY
    return hashlib.md5(sign_string.encode('utf-8')).hexdigest()


def smile_post(endpoint, extra_params):
    params = {
        'uid': settings.SMILE_UID,
        'email': settings.SMILE_EMAIL,
        'time': int(time.time()),
        **extra_params,
    }
    clean_params = {k: v for k, v in params.items() if k != 'sign'}
    params['sign'] = make_sign(clean_params)
    url = f"{settings.SMILE_BASE_URL}/{endpoint}"
    encoded = urlencode(params).encode('utf-8')
    request = Request(url, data=encoded)
    request.add_header('Content-Type', 'application/x-www-form-urlencoded')

    try:
        with urlopen(request, timeout=30) as response:
            payload = response.read().decode('utf-8')
    except HTTPError as exc:
        payload = exc.read().decode('utf-8')
        logger.warning('Smile.one HTTP error %s: %s', exc.code, payload)
    except URLError as exc:
        logger.error('Smile.one connection error: %s', exc)
        raise

    try:
        return json.loads(payload)
    except JSONDecodeError:
        logger.error('Unable to parse Smile.one response: %s', payload)
        return {}


def get_product_list(game_slug):
    game_slug = _normalize_game_slug(game_slug)
    response = smile_post('productlist', {'product': game_slug})
    return response.get('data', {}).get('product', [])


def _normalize_game_slug(game_slug):
    if not game_slug:
        return ''
    return str(game_slug).replace(' ', '').replace('-', '').lower()


def _is_smile_success(response):
    if not isinstance(response, dict):
        return False
    status = response.get('status')
    if status is None:
        status = response.get('code') or response.get('result') or response.get('status_code')
    if status in (200, '200', 'OK', 'ok', 1, '1', True, 'true'):
        return True
    if isinstance(status, str) and status.lower() in ('success', 'successful'):
        return True
    return False


def _extract_smile_username(response):
    if not isinstance(response, dict):
        return None
    candidates = [
        response.get('username'),
        response.get('player_name'),
        response.get('playername'),
        response.get('role'),
        response.get('name'),
    ]
    data = response.get('data', {}) or {}
    candidates += [
        data.get('username'),
        data.get('player_name'),
        data.get('playername'),
        data.get('role'),
        data.get('name'),
    ]
    for value in candidates:
        if value:
            return str(value)
    return None


def verify_player(game_slug, product_id, player_uid, player_sid=''):
    game_slug = _normalize_game_slug(game_slug)
    extra = {
        'product': game_slug,
        'productid': str(product_id),
        'userid': player_uid,
        'zoneid': player_sid or player_uid,
    }
    try:
        response = smile_post('getrole', extra)
        logger.info("Smile.one verify_player response: %s", response)
        username = _extract_smile_username(response)
        if _is_smile_success(response) and username:
            return username
        if username:
            return username
        return None
    except Exception as e:
        logger.error("Smile.one verify_player exception: %s", e)
        return None


def create_order(game_slug, product_id, player_uid, player_sid=''):
    """
    Place an order on Smile.one.
    Returns the smile order ID string on success, None on failure.
    """
    game_slug = _normalize_game_slug(game_slug)
    extra = {
        'product': game_slug,
        'productid': str(product_id),
        'userid': player_uid,
        'zoneid': player_sid or player_uid,
    }
    try:
        response = smile_post('createorder', extra)
        logger.info("Smile.one create_order response: %s", response)
        if _is_smile_success(response):
            order_id = (
                response.get('order_id') or
                response.get('orderid') or
                response.get('game_order') or
                response.get('gameorder') or
                response.get('data', {}).get('order_id') or
                response.get('data', {}).get('orderid') or
                response.get('data', {}).get('game_order')
            )
            return str(order_id) if order_id else None
        logger.error("Smile.one order failed: %s", response)
        return None
    except Exception as e:
        logger.error("Smile.one create_order exception: %s", e)
        return None