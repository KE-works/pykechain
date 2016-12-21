import requests

from kechain2.exceptions import LoginRequiredError
from kechain2.models import Scope, Activity, Part, Property
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

    def __init__(self, url='http://localhost:8000/', check_certificates=True):
        self.session = requests.Session()
        self.api_root = url
        self.headers = {}
        self.auth = None

        if not check_certificates:
            self.session.verify = False

    def login(self, username=None, password=None, token=None):
        """
        Login into KE-chain with either username/password or token

        :param username: username for your user from KE-chain
        :param password: password for your user from KE-chain
        :param token: user authentication token retrieved from KE-chain
        """
        if token:
            self.headers['Authorization'] = 'Token {}'.format(token)
            self.auth = None
        else:
            self.headers.pop('Authorization', None)
            self.auth = (username, password)

    def _build_url(self, resource, **kwargs):
        """helper method to build the correct API url"""
        return self.api_root + API_PATH[resource].format(**kwargs)

    def _request(self, method, url, **kwargs):
        """helper method to perform the request on the API"""
        r = self.session.request(method, url, auth=self.auth, headers=self.headers, **kwargs)

        if r.status_code == 403:
            raise LoginRequiredError(r.json()['results'][0]['detail'])

        return r

    def scopes(self, name=None, status='ACTIVE'):
        r = self._request('GET', self._build_url('scopes'), params={
            'name': name,
            'status': status
        })

        assert r.status_code == 200, "Could not retrieve scopes"

        data = r.json()

        return [Scope(s) for s in data['results']]

    def scope(self, *args, **kwargs):
        _scopes = self.scopes(*args, **kwargs)

        assert len(_scopes) > 0, "No scope fits criteria"
        assert len(_scopes) == 1, "Multiple scopes fit criteria"

        return _scopes[0]

    def activities(self, name=None):
        r = self._request('GET', self._build_url('activities'), params={
            'name': name
        })

        assert r.status_code == 200, "Could not retrieve activities"

        data = r.json()

        return [Activity(a) for a in data['results']]

    def activity(self, *args, **kwargs):
        _activities = self.activities(*args, **kwargs)

        assert len(_activities) > 0, "No activity fits criteria"
        assert len(_activities) == 1, "Multiple activities fit criteria"

        return _activities[0]

    def parts(self, name=None, pk=None, model=None, category='INSTANCE', bucket=None, activity=None):
        """
        Retrieve multiple KE-chain Parts

        :param name: filter on name
        :param pk: filter on primary key
        :param model: filter on model_id
        :param category: filter on category_id
        :param bucket: filter on bucket_id
        :param activity: filter on activity_id
        :return: a list of Parts
        """
        r = self._request('GET', self._build_url('parts'), params={
            'id': pk,
            'name': name,
            'model': model.id if model else None,
            'category': category,
            'bucket': bucket,
            'activity_id': activity
        })

        assert r.status_code == 200, "Could not retrieve parts"

        data = r.json()

        return PartSet((Part(p, client=self) for p in data['results']))

    def part(self, *args, **kwargs):
        """
        Retrieve single KE-chain Part, if multiple parts are returned if will notify and returns the first part.

        :param name: filter on name
        :param pk: filter on primary key
        :param model: filter on model_id
        :param category: filter on category_id
        :param bucket: filter on bucket_id
        :param activity: filter on activity_id
        :return: a single Part or AssertionError
        """
        _parts = self.parts(*args, **kwargs)

        assert len(_parts) > 0, "No part fits criteria"
        assert len(_parts) == 1, "Multiple parts fit criteria"

        return _parts[0]

    def model(self, *args, **kwargs):
        kwargs['category'] = 'MODEL'
        _parts = self.parts(*args, **kwargs)

        assert len(_parts) > 0, "No model fits criteria"
        assert len(_parts) == 1, "Multiple models fit criteria"

        return _parts[0]

    def properties(self, name=None, category='INSTANCE'):
        r = self._request('GET', self._build_url('properties'), params={
            'name': name,
            'category': category
        })

        assert r.status_code == 200, "Could not retrieve properties"

        data = r.json()

        return [Property(p) for p in data['results']]

