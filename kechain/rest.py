import requests

from .part import Part

api_url = 'http://0.0.0.0:8000/api/parts.json'
api_token_admin = '***REMOVED***'
api_token_testuser = '***REMOVED***'


def get_parts():
    headers = {'Authorization': 'Token ' + api_token_admin}

    r = requests.get(api_url, headers=headers)

    assert r.status_code == 200

    raw_data = r.json()

    parts = [Part.from_dict(part_data) for part_data in raw_data['results']]

    return parts
