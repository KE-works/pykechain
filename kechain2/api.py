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

HEADERS = {
    'Authorization': 'Token ***REMOVED***'
}


def api_url(resource, **kwargs):
    return API_ROOT + API_PATH[resource].format(**kwargs)


def parts(name=None, model=None, category='INSTANCE'):
    r = requests.get(api_url('parts'), headers=HEADERS, params={
        'name': name,
        'model': model,
        'category': category
    })

    assert r.status_code == 200, "Could not retrieve parts"

    data = r.json()

    return PartSet(Part(p) for p in data['results'])


def part(*args, **kwargs):
    _parts = parts(*args, **kwargs)

    assert len(_parts) == 1, "Multiple parts fit criteria"

    return _parts[0]


def properties(name=None, category='INSTANCE'):
    r = requests.get(api_url('properties'), headers=HEADERS, params={
        'name': name,
        'category': category
    })

    assert r.status_code == 200, "Could not retrieve properties"

    data = r.json()

    return [Property(p) for p in data['results']]
