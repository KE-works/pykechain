import requests
from envparse import env
from requests.compat import urljoin

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


class Client(object):
    """The KE-chain 2 python client to connect to a KE-chain (version 2) instance.

    :ivar last_request: last executed request. Which is of type `requests.Request`_
    :ivar last_response: last executed response. Which is of type `requests.Response`_
    :ivar last_url: last called api url

    .. _requests.Request: http://docs.python-requests.org/en/master/api/#requests.Request
    .. _requests.Response: http://docs.python-requests.org/en/master/api/#requests.Response
    """

    def __init__(self, url='http://localhost:8000/', check_certificates=True):
        """Create a KE-chain client with given settings.

        :param url: the url of the KE-chain instance to connect to (defaults to http://localhost:8000)
        :param check_certificates: if to check TLS/SSL Certificates. Defaults to True

        Examples
        --------
        >>> from pykechain import Client
        >>> client = Client()

        >>> from pykechain import Client
        >>> client = Client(url='https://default-tst.localhost:9443', check_certificates=False)

        """
        self.session = requests.Session()
        self.api_root = url
        self.headers = {}
        self.auth = None
        self.last_request = None
        self.last_response = None
        self.last_url = None

        if not check_certificates:
            self.session.verify = False

    def __repr__(self):
        return "<pyke Client '{}'>".format(self.api_root)

    @classmethod
    def from_env(cls, env_filename=None):
        """Create a client from environment variable settings.

        :param env_filename: filename of the environment file, defaults to '.env' in the local dir (or parent dir)
        :return: :class:`pykechain.Client`

        Example
        -------

        Initiates the pykechain client from the contents of an environment file. Authentication information is optional
        but ensure that you provide this later in your code. Offered are both username/password authentication and
        user token authentication.

        .. code-block:: none
           :caption: .env
           :name: dot-env

            # User token here (required)
            KECHAIN_TOKEN=...<secret user token>...
            KECHAIN_URL=https://an_url.ke-chain.com

            # or use Basic Auth with username/password
            KECHAIN_USERNAME=...
            KECHAIN_PASSWORD=...


        >>> client = Client().from_env()

        """
        env.read_envfile(env_filename)
        client = cls(url=env('KECHAIN_URL'))

        if env('KECHAIN_TOKEN', None):
            client.login(token=env('KECHAIN_TOKEN'))
        elif env('KECHAIN_USERNAME', '') and env('KECHAIN_PASSWORD', ''):
            client.login(username=env('KECHAIN_USERNAME'), password=env('KECHAIN_PASSWORD'))

        return client

    def login(self, username=None, password=None, token=None):
        """Login into KE-chain with either username/password or token.

        :param username: username for your user from KE-chain
        :param password: password for your user from KE-chain
        :param token: user authentication token retrieved from KE-chain

        Examples
        --------
        Using Token Authentication (retrieve user Token from the KE-chain instance)
        >>> client = Client()
        >>> client.login(token='<some-super-long-secret-token>')

        Using Basic authentications (Username/Password)
        >>> client = Client()
        >>> client.login(username='user', password='pw')

        >>> client = Client()
        >>> client.login('username','password')
        """
        if token:
            self.headers['Authorization'] = 'Token {}'.format(token)
            self.auth = None
        else:
            self.headers.pop('Authorization', None)
            self.auth = (username, password)

    def _build_url(self, resource, **kwargs):
        """Helper method to build the correct API url."""
        return urljoin(self.api_root, API_PATH[resource].format(**kwargs))

    def _request(self, method, url, **kwargs):
        """Helper method to perform the request on the API."""
        self.last_request = None
        self.last_response = self.session.request(method, url, auth=self.auth, headers=self.headers, **kwargs)
        self.last_request = self.last_response.request
        self.last_url = self.last_response.url

        if self.last_response.status_code == requests.codes.forbidden:
            raise ForbiddenError(self.last_response.json()['results'][0]['detail'])

        return self.last_response

    def scopes(self, name=None, pk=None, status='ACTIVE'):
        """Return all scopes visible / accessible for the logged in user.

        :param name: if provided, filter the search for a scope/project by name
        :param pk: if provided, filter the search by scope_id
        :param status: if provided, filter the search for the status. eg. 'ACTIVE', 'TEMPLATE', 'LIBRARY'
        :return: :obj:`list` of :obj:`Scope`
        :raises: NotFoundError

        Example
        -------

        >>> client = Client(url='https://default.localhost:9443', verify=False)
        >>> client.login('admin','pass')
        >>> client.scopes()  # doctest: Ellipsis
        ...

        >>> client.scopes(name="Bike Project")  # doctest: Ellipsis
        ...

        >>> last_request = client.last_request  # doctest: Ellipsis
        ...
        """
        r = self._request('GET', self._build_url('scopes'), params={
            'name': name,
            'id': pk,
            'status': status
        })

        if r.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve scopes")

        data = r.json()

        return [Scope(s, client=self) for s in data['results']]

    def scope(self, *args, **kwargs):
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

    def parts(self, name=None, pk=None, model=None, category='INSTANCE', bucket=None, parent=None, activity=None,
              limit=None, batch=100, **kwargs):
        """Retrieve multiple KE-chain parts.

        :param name: filter on name
        :param pk: filter on primary key
        :param model: filter on model_id
        :param category: filter on category (INSTANCE, MODEL, None)
        :param bucket: filter on bucket_id
        :param parent: filter on the parent_id, returns all childrent of the parent_id
        :param activity: filter on activity_id
        :param limit: limit the return to # items (default unlimited, so return all results)
        :param batch: limit the batch size to # items (defaults to 100 items per batch)
        :param kwargs: additional keyword, value arguments for the api with are passed to the /parts/ api as filters
                       please refer to the full KE-chain 2 REST API documentation.
        :return: :obj:`PartSet`
        :raises: NotFoundError

        Examples
        --------

        Return all parts (defaults to instances) with exact name 'Gears'.
        >>> client = Client(url='https://default.localhost:9443', verify=False)
        >>> client.login('admin','pass')
        >>> client.parts(name='Gears')  # doctest:Ellipsis
        ...

        Return all parts with category is MODEL or category is INSTANCE.
        >>> client.parts(name='Gears', category=None)  # doctest:Ellipsis
        ...

        Return a maximum of 5 parts
        >>> client.parts(limit=5)  # doctest:Ellipsis
        ...
        """
        # if limit is provided and the batchsize is bigger than the limit, ensure that the batch size is maximised
        if limit and limit < batch:
            batch = limit

        request_params = {
            'id': pk,
            'name': name,
            'model': model.id if model else None,
            'category': category,
            'bucket': bucket,
            'parent': parent,
            'activity_id': activity,
            'limit': batch
        }

        if kwargs:
            request_params.update(**kwargs)

        r = self._request('GET', self._build_url('parts'), params=request_params)

        if r.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve parts")

        data = r.json()

        part_results = data['results']

        if batch and data.get('next'):
            while data['next']:
                # respect the limit if set to > 0
                if limit and len(part_results) >= limit:
                    break
                r = self._request('GET', data['next'])
                data = r.json()
                part_results.extend(data['results'])

        return PartSet((Part(p, client=self) for p in part_results))

    def part(self, *args, **kwargs):
        """Retrieve single KE-chain part.

        Uses the same interface as the `part` method but returns only a single pykechain `Part` instance.

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
        """Retrieve single KE-chain part model.

        Uses the same interface as the `part` method but returns only a single pykechain `Part` instance.

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

    def properties(self, name=None, pk=None, category='INSTANCE'):
        """Retrieve properties.

        :param name: name to limit the search for.
        :param pk: primary key or id (UUID) of the property to search for
        :param category: filter the properties by category. Defaults to INSTANCE. Other options MODEL or None
        :return: :obj:`list` of :obj:`Property`
        :raises: NotFoundError
        """
        r = self._request('GET', self._build_url('properties'), params={
            'name': name,
            'id': pk,
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
