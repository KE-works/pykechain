import requests

from kechain2.models import Part, Property, Scope, Activity
from kechain2.sets import PartSet

API_ROOT = 'http://0.0.0.0:8000/'

API_PATH = {
    'scopes': 'api/scopes.json',
    'activities': 'api/activities.json',
    'parts': 'api/parts.json',
    'part': 'api/parts/{part_id}',
    'properties': 'api/properties.json',
    'property': 'api/properties/{property_id}.json',
    'property_upload': 'api/properties/{property_id}/upload'
}

HEADERS = {}

session = requests.Session()


def api_url(resource, **kwargs):
    return API_ROOT + API_PATH[resource].format(**kwargs)


def login(token):
    HEADERS['Authorization'] = 'Token {}'.format(token)


def scopes(name=None, status='ACTIVE'):
    r = session.get(api_url('scopes'), headers=HEADERS, params={
        'name': name,
        'status': status
    })

    assert r.status_code == 200, "Could not retrieve scopes"

    data = r.json()

    return [Scope(s) for s in data['results']]


def scope(*args, **kwargs):
    _scopes = scopes(*args, **kwargs)

    assert len(_scopes) > 0, "No scope fits criteria"
    assert len(_scopes) == 1, "Multiple scopes fit criteria"

    return _scopes[0]


def activities(name=None):
    r = session.get(api_url('activities'), headers=HEADERS, params={
        'name': name
    })

    assert r.status_code == 200, "Could not retrieve activities"

    data = r.json()

    return [Activity(a) for a in data['results']]


def activity(*args, **kwargs):
    _activities = activities(*args, **kwargs)

    assert len(_activities) > 0, "No activity fits criteria"
    assert len(_activities) == 1, "Multiple activities fit criteria"

    return _activities[0]


def parts(name=None, pk=None, model=None, category='INSTANCE', bucket=None, activity=None):
    r = session.get(api_url('parts'), headers=HEADERS, params={
        'id': pk,
        'name': name,
        'model': model.id if model else None,
        'category': category,
        'bucket': bucket,
        'activity_id': activity
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
    r = session.get(api_url('properties'), headers=HEADERS, params={
        'name': name,
        'category': category
    })

    assert r.status_code == 200, "Could not retrieve properties"

    data = r.json()

    return [Property(p) for p in data['results']]
