import hashlib
from typing import Mapping


def normalize_smileone_payload(payload: Mapping) -> dict:
    return {
        str(key): str(value).strip()
        for key, value in payload.items()
        if key != 'sign' and value is not None and str(value).strip() != ''
    }


def generate_smileone_sign(payload: Mapping, secret_key: str) -> str:
    clean_payload = normalize_smileone_payload(payload)
    sorted_items = sorted(clean_payload.items(), key=lambda item: item[0])
    query_string = '&'.join(f"{key}={value}" for key, value in sorted_items)
    if query_string:
        query_string = f"{query_string}&{secret_key}"
    else:
        query_string = secret_key
    first_hash = hashlib.md5(query_string.encode('utf-8')).hexdigest()
    return hashlib.md5(first_hash.encode('utf-8')).hexdigest()


def build_smileone_sign_string(payload: Mapping, secret_key: str) -> str:
    clean_payload = normalize_smileone_payload(payload)
    sorted_items = sorted(clean_payload.items(), key=lambda item: item[0])
    query_string = '&'.join(f"{key}={value}" for key, value in sorted_items)
    return f"{query_string}&{secret_key}" if query_string else secret_key
