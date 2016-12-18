import requests

from kechain2.exceptions import LoginRequiredError
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

    def login(self, username=None, password=None, token=None, url=None, check_certificate=True):
        """
        Login into KE-chain with either username/password or token
        :param username: username for your user from KE-chain
        :param password: password for your user from KE-chain
        :param token: user authentication token retrieved from KE-chain
        :param url: url where KE-chain lives, defaults to localhost:8000 for development
        :param check_certificate: checks ssl certificates, set to False to ignore https (self-signed) certificates
        """
        if url:
            self.api_root = url
        if not check_certificate:
            self.session = requests.Session(verify=False)
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
            raise LoginRequiredError

        return r

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

        return PartSet((Part(p) for p in data['results']), client=self)

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
