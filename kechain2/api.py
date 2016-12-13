import requests

from kechain2.models import Part, Property
from kechain2.sets import PartSet

API_ROOT = 'http://0.0.0.0:8000/'

API_PATH = {
    'parts': 'api/parts.json',
    'properties': 'api/properties.json',
    'property': 'api/properties/{property_id}.json',
    'property_upload': 'api/properties/{property_id}/upload'
}

HEADERS = {}


def api_url(resource, **kwargs):
    return API_ROOT + API_PATH[resource].format(**kwargs)


def login(token):
    HEADERS['Authorization'] = 'Token {}'.format(token)


def parts(name=None, pk=None, model=None, category='INSTANCE'):
    r = requests.get(api_url('parts'), headers=HEADERS, params={
        'id': pk,
        'name': name,
        'model': model.id if model else None,
        'category': category
    })

    assert r.status_code == 200, "Could not retrieve parts"

    data = r.json()

    return PartSet(Part(p) for p in data['results'])


def part(*args, **kwargs):
    _parts = parts(*args, **kwargs)

    assert len(_parts) > 0, "No part fits criteria"
    assert len(_parts) == 1, "Multiple parts fit criteria"

    return _parts[0]


def model(*args, **kwargs):
    kwargs['category'] = 'MODEL'
    _parts = parts(*args, **kwargs)

    assert len(_parts) > 0, "No model fits criteria"
    assert len(_parts) == 1, "Multiple models fit criteria"

    return _parts[0]


def properties(name=None, category='INSTANCE'):
    r = requests.get(api_url('properties'), headers=HEADERS, params={
        'name': name,
        'category': category
    })

    assert r.status_code == 200, "Could not retrieve properties"

    data = r.json()

    return [Property(p) for p in data['results']]
