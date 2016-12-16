import requests

from kechain2.models import Part
from kechain2.sets import PartSet

API_PATH = {
    'scopes': 'api/scopes.json',
    'activities': 'api/activities.json',
    'parts': 'api/parts.json',
    'part': 'api/parts/{part_id}',
    'properties': 'api/properties.json',
    'property': 'api/properties/{property_id}.json',
    'property_upload': 'api/properties/{property_id}/upload'
}


class Client(object):

    def __init__(self):
        self.session = requests.Session()
        self.api_root = 'http://localhost:8000/'
        self.headers = {}
        self.auth = None

    def login(self, username=None, password=None, token=None):
        if token:
            self.headers['Authorization'] = 'Token {}'.format(token)
            self.auth = None
        else:
            self.headers.pop('Authorization', None)
            self.auth = (username, password)

    def build_url(self, resource, **kwargs):
        return self.api_root + API_PATH[resource].format(**kwargs)

    def parts(self, name=None, pk=None, model=None, category='INSTANCE', bucket=None, activity=None):
        r = self.session.get(self.build_url('parts'), auth=self.auth, headers=self.headers, params={
            'id': pk,
            'name': name,
            'model': model.id if model else None,
            'category': category,
            'bucket': bucket,
            'activity_id': activity
        })

        assert r.status_code == 200, "Could not retrieve parts"

        data = r.json()

        return PartSet((Part(p) for p in data['results']), client=self)

    def part(self, *args, **kwargs):
        _parts = self.parts(*args, **kwargs)

        assert len(_parts) > 0, "No part fits criteria"
        assert len(_parts) == 1, "Multiple parts fit criteria"

        return _parts[0]
