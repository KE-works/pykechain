import requests

from .exceptions import LoginRequiredError, NotFoundError, MultipleFoundError
from .models import Scope, Activity, Part, Property
from .sets import PartSet

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
        """
        The KE-chain 2 python client to connect to a KE-chain (version 2) instance.

        :param url: the url of the KE-chain instance to connect to (defaults to http://localhost:8000)
        :param check_certificates: if to check TLS/SSL Certificates. Defaults to True

        Examples:
        ---------
        >>> from pykechain import Client
        >>> kec = Client(url='https://default-tst.localhost:9443', check_certificates=False)

        >>> from pykechain import Client
        >>> kec = Client()
        """
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

        Examples:
        ---------
        Token Authentication::
        >>> from pykechain import Client
        >>> kec = Client()
        >>> kec.login(token='<some-super-long-secret-token-you-download-from-your-kechain-user-profile>')

        Basic Authentication::
        >>> from pykechain import Client
        >>> kec = Client()
        >>> kec.login(username='demo_user', password='visible_password')
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

        if r.status_code == requests.codes.forbidden:
            raise LoginRequiredError(r.json()['results'][0]['detail'])

        return r

    def scopes(self, name=None, status='ACTIVE'):
        """
        Returns all scopes visible / accessible for the logged in user

        :param name: if provided, filter the search for a scope/project by name
        :param status: if provided, filter the search for the status. eg. 'ACTIVE', 'TEMPLATE', 'LIBRARY'
        :return: list of scopes
        :rtype: list of Scope
        """
        r = self._request('GET', self._build_url('scopes'), params={
            'name': name,
            'status': status
        })

        if r.status_code != requests.codes.ok:
            raise NotFoundError("Could not retrieve scopes")

        data = r.json()

        return [Scope(s) for s in data['results']]

    def scope(self, *args, **kwargs):
        """
        Returns a single scope based on the provided name.
        Returns a AssertionError if no scopes could be found or multiple scopes are retrieved

        :param args:
        :param kwargs:
        :return: a single Scope
        :rtype: Scope
        """
        _scopes = self.scopes(*args, **kwargs)

        if len(_scopes) == 0:
            raise NotFoundError("No scope fits criteria")
        if len(_scopes) != 1:
            raise MultipleFoundError("Multiple scopes fit criteria")

        return _scopes[0]

    def activities(self, name=None):
        """
        Searches on activities with optional name filter
        If no activity could be found, returns an Exception

        :param name: filter the activities on Name
        :return: list of activities
        :rtype: list of Activity
        """
        r = self._request('GET', self._build_url('activities'), params={
            'name': name
        })

        if r.status_code != requests.codes.ok:
            raise NotFoundError("Could not retrieve activities")

        data = r.json()

        return [Activity(a) for a in data['results']]

    def activity(self, *args, **kwargs):
        """
        searches for a single activity
        returns and error if the activity name is not found, or multiple activities are returned

        :param name: Name of the activity to search
        :return: Activity with name
        :rtype: Activity
        """
        _activities = self.activities(*args, **kwargs)

        if len(_activities) == 0:
            raise NotFoundError("No activity fits criteria")
        # TODO: could also be a warning (see warnings.warn)
        if len(_activities) != 1:
            raise MultipleFoundError("Multiple activities fit criteria")

        return _activities[0]

    def parts(self, name=None, pk=None, model=None, category='INSTANCE', bucket=None, activity=None):
        """
        Retrieve multiple KE-chain Parts

        :param name: filter on name
        :param pk: filter on primary key
        :param model: filter on model_id
        :param category: filter on category (INSTANCE, MODEL, None)
        :param bucket: filter on bucket_id
        :param activity: filter on activity_id
        :return: a list of Parts
        :rtype: PartSet
        """
        r = self._request('GET', self._build_url('parts'), params={
            'id': pk,
            'name': name,
            'model': model.id if model else None,
            'category': category,
            'bucket': bucket,
            'activity_id': activity
        })

        if r.status_code != requests.codes.ok:
            raise NotFoundError("Could not retrieve parts")

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
        :rtype: Part
        """
        _parts = self.parts(*args, **kwargs)

        if len(_parts) == 0:
            raise NotFoundError("No part fits criteria")
        # TODO: could also be a warning (see warnings.warn)
        if len(_parts) != 1:
            raise MultipleFoundError("Multiple parts fit criteria")

        return _parts[0]

    def model(self, *args, **kwargs):
        kwargs['category'] = 'MODEL'
        _parts = self.parts(*args, **kwargs)

        if len(_parts) == 0:
            raise NotFoundError("No model fits criteria")
        # TODO: could also be a warning (see warnings.warn)
        if len(_parts) != 1:
            raise MultipleFoundError("Multiple model fit criteria")

        return _parts[0]

    def properties(self, name=None, category='INSTANCE'):
        """
        retrieves properties by name

        :param name: name to limit the search for.
        :param category: filter the properties by category. Defaults to INSTANCE. Other options MODEL or None
        :return: list of properties
        :rtype: list of Property
        """
        r = self._request('GET', self._build_url('properties'), params={
            'name': name,
            'category': category
        })

        if r.status_code != requests.codes.ok:
            raise NotFoundError("Could not retrieve properties")

        data = r.json()

        return [Property(p) for p in data['results']]
