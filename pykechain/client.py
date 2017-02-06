from typing import Dict, Tuple, Optional, Any, List  # flake8: noqa

import requests
from requests.compat import urljoin  # type: ignore
from envparse import env

from .exceptions import ForbiddenError, NotFoundError, MultipleFoundError, APIError
from .models import Scope, Activity, Part, PartSet, Property

API_PATH = {
    'scopes': 'api/scopes.json',
    'activities': 'api/activities.json',
    'activity': 'api/activities/{activity_id}.json',
    'association': 'api/associations/{association_id}.json',
    'parts': 'api/parts.json',
    'part': 'api/parts/{part_id}.json',
    'properties': 'api/properties.json',
    'property': 'api/properties/{property_id}.json',
    'property_upload': 'api/properties/{property_id}/upload',
    'property_download': 'api/properties/{property_id}/download'
}

env.read_envfile()


class Client(object):
    """The KE-chain 2 python client to connect to a KE-chain (version 2) instance."""

    def __init__(self, url='http://localhost:8000/', check_certificates=True):
        # type: (str, bool) -> None
        """Create a KE-chain client with given settings.

        :param url: the url of the KE-chain instance to connect to (defaults to http://localhost:8000)
        :param check_certificates: if to check TLS/SSL Certificates. Defaults to True

        Examples
        --------
        >>> from pykechain import Client
        >>> kec = Client()

        >>> from pykechain import Client
        >>> kec = Client(url='https://default-tst.localhost:9443', check_certificates=False)

        """
        self.session = requests.Session()
        self.api_root = url
        self.headers = {}  # type: Dict[str, str]
        self.auth = None  # type: Optional[Tuple[str, str]]

        if not check_certificates:
            self.session.verify = False

    @classmethod
    def from_env(cls):
        # type: () -> Client
        """Create a client from environment variable settings."""
        client = cls(url=env('KECHAIN_URL'))
        client.login(token=env('KECHAIN_TOKEN'))

        return client

    def login(self, username=None, password=None, token=None):
        # type: (Optional[str], Optional[str], Optional[str]) -> None
        """Login into KE-chain with either username/password or token.

        :param username: username for your user from KE-chain
        :param password: password for your user from KE-chain
        :param token: user authentication token retrieved from KE-chain

        Examples
        --------
        Using Token Authentication (retrieve user Token from the KE-chain instance)
        >>> kec = Client()
        >>> kec.login(token='<some-super-long-secret-token>')

        Using Basic authentications (Username/Password)
        >>> kec = Client()
        >>> kec.login(username='user', password='pw')

        >>> kec = Client()
        >>> kec.login('username','password')
        """
        self.headers.pop('Authorization', None)
        self.auth = None

        if token:
            self.headers['Authorization'] = 'Token {}'.format(token)
        elif username is not None and password is not None:
            self.auth = (username, password)

    def _build_url(self, resource, **kwargs):
        # type: (str, **str) -> str
        """Helper method to build the correct API url."""
        return urljoin(self.api_root, API_PATH[resource].format(**kwargs))

    def _request(self, method, url, **kwargs):
        # type: (str, str, **Any) -> requests.Response
        """Helper method to perform the request on the API."""
        r = self.session.request(method, url, auth=self.auth, headers=self.headers, **kwargs)

        if r.status_code == requests.codes.forbidden:
            raise ForbiddenError(r.json()['results'][0]['detail'])

        return r

    def scopes(self, name=None, id=None, status='ACTIVE'):
        # type: (Optional[str], Optional[str], Optional[str]) -> List[Scope]
        """Return all scopes visible / accessible for the logged in user.

        :param name: if provided, filter the search for a scope/project by name
        :param id: if provided, filter the search by scope_id
        :param status: if provided, filter the search for the status. eg. 'ACTIVE', 'TEMPLATE', 'LIBRARY'
        :return: :obj:`list` of :obj:`Scope`
        :raises: NotFoundError

        Example
        -------

        >>> kec = Client(url='https://default.localhost:9443', verify=False)
        >>> kec.login('admin','pass')
        >>> kec.scopes()  # doctest: Ellipsis
        ...

        >>> kec.scopes(name="Bike Project") # doctest: Ellipsis
        ...
        """
        r = self._request('GET', self._build_url('scopes'), params={
            'name': name,
            'id': id,
            'status': status
        })

        if r.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve scopes")

        data = r.json()

        return [Scope(s, client=self) for s in data['results']]

    def scope(self, *args, **kwargs):
        # type: (*Any, **Any) -> Scope
        """Return a single scope based on the provided name.

        :return: a single :obj:`Scope`
        :raises: NotFoundError, MultipleFoundError
        """
        _scopes = self.scopes(*args, **kwargs)

        if len(_scopes) == 0:
            raise NotFoundError("No scope fits criteria")
        if len(_scopes) != 1:
            raise MultipleFoundError("Multiple scopes fit criteria")

        return _scopes[0]

    def activities(self, name=None, scope=None):
      # type: (Optional[str]) -> List[Activity]
        """Search on activities with optional name filter.

        :param name: filter the activities by name
        :param scope: filter by scope id
        :return: :obj:`list` of :obj:`Activity`
        :raises: NotFoundError
        """
        r = self._request('GET', self._build_url('activities'), params={
            'name': name,
            'scope': scope
        })

        if r.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve activities")

        data = r.json()

        return [Activity(a, client=self) for a in data['results']]

    def activity(self, *args, **kwargs):
        # type: (*Any, **Any) -> Activity
        """Search for a single activity.

        :param name: Name of the activity to search
        :return: a single :obj:`Activity`
        :raises: NotFoundError, MultipleFoundError
        """
        _activities = self.activities(*args, **kwargs)

        if len(_activities) == 0:
            raise NotFoundError("No activity fits criteria")
        if len(_activities) != 1:
            raise MultipleFoundError("Multiple activities fit criteria")

        return _activities[0]

    def parts(self,
              name=None,            # type: Optional[str]
              pk=None,              # type: Optional[str]
              model=None,           # type: Optional[Part]
              category='INSTANCE',  # type: Optional[str]
              bucket=None,          # type: Optional[str]
              activity=None         # type: Optional[str]
              ):
        # type: (...) -> PartSet
        """Retrieve multiple KE-chain parts.

        :param name: filter on name
        :param pk: filter on primary key
        :param model: filter on model_id
        :param category: filter on category (INSTANCE, MODEL, None)
        :param bucket: filter on bucket_id
        :param activity: filter on activity_id
        :return: :obj:`PartSet`
        :raises: NotFoundError
        """
        r = self._request('GET', self._build_url('parts'), params={
            'id': pk,
            'name': name,
            'model': model.id if model else None,
            'category': category,
            'bucket': bucket,
            'activity_id': activity
        })

        if r.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve parts")

        data = r.json()

        return PartSet((Part(p, client=self) for p in data['results']))

    def part(self, *args, **kwargs):
        # type: (*Any, **Any) -> Part
        """Retrieve single KE-chain part.

        :return: a single :obj:`Part`
        :raises: NotFoundError, MultipleFoundError
        """
        _parts = self.parts(*args, **kwargs)

        if len(_parts) == 0:
            raise NotFoundError("No part fits criteria")
        if len(_parts) != 1:
            raise MultipleFoundError("Multiple parts fit criteria")

        return _parts[0]

    def model(self, *args, **kwargs):
        # type: (*Any, **Any) -> Part
        """Retrieve single KE-chain model.

        :return: a single :obj:`Part`
        :raises: NotFoundError, MultipleFoundError
        """
        kwargs['category'] = 'MODEL'
        _parts = self.parts(*args, **kwargs)

        if len(_parts) == 0:
            raise NotFoundError("No model fits criteria")
        if len(_parts) != 1:
            raise MultipleFoundError("Multiple model fit criteria")

        return _parts[0]

    def properties(self, name=None, category='INSTANCE'):
        # type: (Optional[str], Optional[str]) -> List[Property]
        """Retrieve properties.

        :param name: name to limit the search for.
        :param category: filter the properties by category. Defaults to INSTANCE. Other options MODEL or None
        :return: :obj:`list` of :obj:`Property`
        :raises: NotFoundError
        """
        r = self._request('GET', self._build_url('properties'), params={
            'name': name,
            'category': category
        })

        if r.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve properties")

        data = r.json()

        return [Property.create(p, client=self) for p in data['results']]

    def create_activity(self, process, name, activity_class="UserTask"):
        """Create a new activity.

        :param process: parent process id
        :param name: new activity name
        :param activity_class: type of activity: UserTask (default) or Subprocess
        :return: Activity
        """
        data = {
            "name": name,
            "process": process,
            "activity_class": activity_class
        }

        r = self._request('POST', self._build_url('activities'), data=data)

        if r.status_code != 201:
            raise APIError("Could not create activity")

        data = r.json()

        return Activity(data['results'][0], client=self)

    def create_part(self, parent, model, name=None):
        """Create a new part from a given model under a given parent.

        :param parent: parent part instance
        :param model: target part model
        :param name: new part name
        :return: Part
        """
        assert parent.category == 'INSTANCE'
        assert model.category == 'MODEL'

        if not name:
            name = model.name

        data = {
            "name": name,
            "parent": parent.id,
            "model": model.id
        }

        r = self._request('POST', self._build_url('parts'),
                          params={"select_action": "new_instance"},
                          data=data)

        if r.status_code != 201:
            raise APIError("Could not create part: {}".format(name))

        data = r.json()

        return Part(data['results'][0], client=self)
