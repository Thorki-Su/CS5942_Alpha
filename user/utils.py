# user/utils.py

import requests
import re

def normalize_uk_postcode(postcode):
    postcode = postcode.upper().strip().replace(' ', '')
    # 插入空格到标准格式，例如 AB253DD -> AB25 3DD
    return re.sub(r'([A-Z]{1,2}\d{1,2})(\d[A-Z]{2})', r'\1 \2', postcode)

def is_valid_aberdeen_postcode(postcode):
    postcode = normalize_uk_postcode(postcode)
    resp_validate = requests.get(f'https://api.postcodes.io/postcodes/{postcode}/validate')
    if resp_validate.status_code != 200 or not resp_validate.json().get('result', False):
        return False

    resp_lookup = requests.get(f'https://api.postcodes.io/postcodes/{postcode}')
    if resp_lookup.status_code != 200:
        return False

    data = resp_lookup.json().get('result')
    if not data:
        return False

    district = data.get('admin_district', '').lower()
    if 'aberdeen' in district:
        return True
    return False

def geocode_address(address):
    # 若地址中包含 null 等无效片段，先过滤掉
    clean_parts = [part.strip() for part in str(address).split(',') if part and part.lower() != 'null']
    
    # 为保险起见加上国家
    cleaned_address = ', '.join(clean_parts + ['UK'])

    print(f"尝试解析地址：{cleaned_address}")

    url = f"https://nominatim.openstreetmap.org/search"
    params = {
        'q': cleaned_address,
        'format': 'json',
        'limit': 1,
    }
    headers = {
        'User-Agent': 'Django Volunteer App (for testing only)'
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        if data:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            return lat, lon
    except Exception as e:
        print(f"[Geocode ERROR] 地址解析失败：{cleaned_address} → {e}")
    return None, None

