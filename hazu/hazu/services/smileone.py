import json
import logging
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

try:
    import requests
except ImportError:
    requests = None

from hazu.constants.products import SMILE_API_PREFIX, SMILE_DEFAULT_GAME_NAME, SMILE_FORM_CONTENT_TYPE
from hazu.utils.signature import build_smileone_sign_string, generate_smileone_sign

logger = logging.getLogger(__name__)


class SmileOneError(Exception):
    pass


def _validate_smileone_config():
    if not getattr(settings, 'SMILE_UID', None):
        raise ImproperlyConfigured('SMILE_UID must be configured for Smile.one integration.')
    if not getattr(settings, 'SMILE_EMAIL', None):
        raise ImproperlyConfigured('SMILE_EMAIL must be configured for Smile.one integration.')
    if not getattr(settings, 'SMILE_KEY', None):
        raise ImproperlyConfigured('SMILE_KEY must be configured for Smile.one integration.')
    if not getattr(settings, 'SMILE_BASE_URL', None):
        raise ImproperlyConfigured('SMILE_BASE_URL must be configured for Smile.one integration.')


def _normalize_game_slug(game_slug: str) -> str:
    if not game_slug:
        return SMILE_DEFAULT_GAME_NAME
    return str(game_slug).strip().replace(' ', '').replace('-', '').lower() or SMILE_DEFAULT_GAME_NAME


def _build_url(endpoint: str) -> str:
    base = settings.SMILE_BASE_URL.rstrip('/')
    prefix = getattr(settings, 'SMILE_API_PREFIX', SMILE_API_PREFIX).strip('/')
    return f"{base}/{prefix}/{endpoint.lstrip('/')}"


def _build_payload(extra_params: dict) -> dict:
    _validate_smileone_config()
    payload = {
        'uid': str(settings.SMILE_UID).strip(),
        'email': str(settings.SMILE_EMAIL).strip(),
        'time': int(time.time()),
        **{k: str(v).strip() for k, v in extra_params.items() if v is not None},
    }
    payload['sign'] = generate_smileone_sign(payload, str(settings.SMILE_KEY).strip())
    logger.debug('SmileOne payload built: %s', payload)
    logger.debug('SmileOne sign string: %s', build_smileone_sign_string(payload, str(settings.SMILE_KEY).strip()))
    logger.debug('SmileOne generated sign: %s', payload['sign'])
    return payload


def _parse_smileone_response(response_text: str) -> dict:
    try:
        parsed = json.loads(response_text)
        logger.debug('SmileOne raw response JSON: %s', parsed)
        return parsed
    except json.JSONDecodeError:
        logger.error('Unable to parse Smile.one response as JSON: %s', response_text)
        raise SmileOneError('Invalid Smile.one response format')


def _http_post_form(url: str, payload: dict, timeout: int = 30) -> dict:
    logger.info('SmileOne request URL: %s', url)
    logger.info('SmileOne outgoing payload: %s', payload)
    headers = {
        'Content-Type': SMILE_FORM_CONTENT_TYPE,
        'User-Agent': 'Hazumake/1.0 (+https://hazumake.com)',
    }

    if requests is not None:
        try:
            response = requests.post(url, data=payload, timeout=timeout, headers=headers)
            logger.info('SmileOne response status: %s', response.status_code)
            logger.info('SmileOne response body: %s', response.text)
            response.raise_for_status()
            return _parse_smileone_response(response.text)
        except requests.exceptions.HTTPError as exc:
            body = exc.response.text if exc.response is not None else ''
            logger.warning('SmileOne HTTP error %s: %s', exc.response.status_code if exc.response is not None else 'N/A', body)
            return _parse_smileone_response(body)
        except requests.exceptions.RequestException as exc:
            logger.error('SmileOne connection error: %s', exc)
            raise SmileOneError(f'Smile.one connection failed: {exc}')

    data = urlencode(payload).encode('utf-8')
    request = Request(url, data=data)
    request.add_header('Content-Type', SMILE_FORM_CONTENT_TYPE)
    request.add_header('User-Agent', 'Hazumake/1.0 (+https://hazumake.com)')

    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode('utf-8')
            logger.info('SmileOne response status: %s', response.status)
            logger.info('SmileOne response body: %s', body)
            return _parse_smileone_response(body)
    except HTTPError as exc:
        body = exc.read().decode('utf-8', errors='ignore')
        logger.warning('SmileOne HTTP error %s: %s', exc.code, body)
        return _parse_smileone_response(body)
    except URLError as exc:
        logger.error('SmileOne connection error: %s', exc)
        raise SmileOneError(f'Smile.one connection failed: {exc}')


def _is_smile_success(response: dict) -> bool:
    if not isinstance(response, dict):
        return False
    status = response.get('status') or response.get('code') or response.get('result') or response.get('status_code')
    if isinstance(status, str):
        status = status.lower()
        return status in ('200', 'ok', 'success', 'successful', '1', 'true')
    return status in (200, 1, True)


def _extract_smile_username(response: dict) -> str | None:
    data = response.get('data') or {}
    candidates = [
        response.get('username'),
        response.get('player_name'),
        response.get('playername'),
        response.get('role'),
        response.get('name'),
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


def _extract_smile_order_id(response: dict) -> str | None:
    data = response.get('data') or {}
    order_id = (
        response.get('order_id') or
        response.get('orderid') or
        response.get('game_order') or
        response.get('gameorder') or
        data.get('order_id') or
        data.get('orderid') or
        data.get('game_order') or
        data.get('trade_no') or
        data.get('order_no')
    )
    return str(order_id) if order_id else None


def get_product_list(game_slug: str) -> list:
    game_slug = _normalize_game_slug(game_slug)
    payload = _build_payload({'product': game_slug})
    response = _http_post_form(_build_url('productlist'), payload)
    if _is_smile_success(response):
        return response.get('data', {}).get('product', []) or []
    logger.warning('SmileOne get_product_list failed: %s', response)
    return []


def get_role(game_slug: str, product_id: str, player_uid: str, player_sid: str = '') -> str | None:
    game_slug = _normalize_game_slug(game_slug)
    payload = _build_payload({
        'product': game_slug,
        'productid': str(product_id).strip(),
        'userid': str(player_uid).strip(),
        'zoneid': str(player_sid).strip() or str(player_uid).strip(),
    })
    response = _http_post_form(_build_url('getrole'), payload)
    logger.info('SmileOne get_role response: %s', response)
    if _is_smile_success(response):
        return _extract_smile_username(response)
    logger.warning('SmileOne get_role failed: %s', response)
    return _extract_smile_username(response)


def create_order(game_slug: str, product_id: str, player_uid: str, player_sid: str = '') -> str | None:
    game_slug = _normalize_game_slug(game_slug)
    payload = _build_payload({
        'product': game_slug,
        'productid': str(product_id).strip(),
        'userid': str(player_uid).strip(),
        'zoneid': str(player_sid).strip() or str(player_uid).strip(),
    })
    response = _http_post_form(_build_url('createorder'), payload)
    logger.info('SmileOne create_order response: %s', response)
    if _is_smile_success(response):
        order_id = _extract_smile_order_id(response)
        if order_id:
            return order_id
    logger.error('SmileOne create_order failed: %s', response)
    return None
