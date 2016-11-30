import requests

from .part import Part

api_url = 'http://0.0.0.0:8000/api/parts.json'
api_token_admin = 'b54d6a288bf8d7ace29995a958b69d915db39650'
api_token_testuser = '46ad93fb958d1265c6fec252abc603b3c59b99fd'


def get_parts():
    headers = {'Authorization': 'Token ' + api_token_admin}

    r = requests.get(api_url, headers=headers)

    assert r.status_code == 200

    raw_data = r.json()

    parts = [Part.from_dict(part_data) for part_data in raw_data['results']]

    return parts
