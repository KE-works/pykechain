from typing import Dict, Tuple, Optional, Any, List  # flake8: noqa

import requests
import warnings
from envparse import env
from requests.compat import urljoin, urlparse  # type: ignore

from pykechain.enums import Category, KechainEnv
from .__about__ import version
from .exceptions import ForbiddenError, NotFoundError, MultipleFoundError, APIError, ClientError, IllegalArgumentError
from .models import Scope, Activity, Part, PartSet, Property

API_PATH = {
    'scopes': 'api/scopes.json',
    'scope': 'api/scopes/{scope_id}.json',
    'activities': 'api/activities.json',
    'activity': 'api/activities/{activity_id}.json',
    'parts': 'api/parts.json',
    'part': 'api/parts/{part_id}.json',
    'properties': 'api/properties.json',
    'property': 'api/properties/{property_id}.json',
    'property_upload': 'api/properties/{property_id}/upload',
    'property_download': 'api/properties/{property_id}/download',
    'widgets_config': 'api/widget_config.json',
    'widget_config': 'api/widget_config/{widget_config_id}.json',
    'users': 'api/users.json'
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
        # type: (str, bool) -> None
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
        parsed_url = urlparse(url)
        if not (parsed_url.scheme and parsed_url.netloc):
            raise ClientError("Please provide a valid URL to a KE-chain instance")

        self.session = requests.Session()
        self.api_root = url
        self.headers = {'X-Requested-With': 'XMLHttpRequest', 'PyKechain-Version': version}  # type: Dict[str, str]
        self.auth = None  # type: Optional[Tuple[str, str]]
        self.last_request = None  # type: Optional[requests.PreparedRequest]
        self.last_response = None  # type: Optional[requests.Response]
        self.last_url = None  # type: Optional[str]

        if not check_certificates:
            self.session.verify = False

    def __repr__(self):  # pragma: no cover
        return "<pyke Client '{}'>".format(self.api_root)

    @classmethod
    def from_env(cls, env_filename=None):
        # type: (Optional[str]) -> Client
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

            # optional add a scope name or scope id
            KECHAIN_SCOPE=...
            KECHAIN_SCOPE_ID=...

        >>> client = Client().from_env()

        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            env.read_envfile(env_filename)
        client = cls(url=env(KechainEnv.KECHAIN_URL))

        if env(KechainEnv.KECHAIN_TOKEN, None):
            client.login(token=env(KechainEnv.KECHAIN_TOKEN))
        elif env(KechainEnv.KECHAIN_USERNAME, None) and env(KechainEnv.KECHAIN_PASSWORD, None):
            client.login(username=env(KechainEnv.KECHAIN_USERNAME), password=env(KechainEnv.KECHAIN_PASSWORD))

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
        elif username and password:
            self.headers.pop('Authorization', None)
            self.auth = (username, password)

    def _build_url(self, resource, **kwargs):
        # type: (str, **str) -> str
        """Build the correct API url."""
        return urljoin(self.api_root, API_PATH[resource].format(**kwargs))

    def _retrieve_users(self):
        """
        Retrieve user objects of the entire administration.

        :return: `list` of :obj:`User`
        -------

        """
        users_url = self._build_url('users')
        response = self._request('GET', users_url)
        users = response.json()
        return users

    def _request(self, method, url, **kwargs):
        # type: (str, str, **Any) -> requests.Response
        """Perform the request on the API."""
        self.last_request = None
        self.last_response = self.session.request(method, url, auth=self.auth, headers=self.headers, **kwargs)
        self.last_request = self.last_response.request
        self.last_url = self.last_response.url

        if self.last_response.status_code == requests.codes.forbidden:
            raise ForbiddenError(self.last_response.json()['results'][0]['detail'])

        return self.last_response

    def scopes(self, name=None, pk=None, status='ACTIVE'):
        # type: (Optional[str], Optional[str], Optional[str]) -> List[Scope]
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

    def activities(self, name=None, pk=None, scope=None, **kwargs):
        # type: (Optional[str], Optional[str], Optional[str], **Any) -> List[Activity]
        """Search on activities with optional name filter.

        :param pk: id (primary key) of the activity to retrieve
        :param name: filter the activities by name
        :param scope: filter by scope id
        :return: :obj:`list` of :obj:`Activity`
        :raises: NotFoundError
        """
        request_params = {
            'id': pk,
            'name': name,
            'scope': scope
        }
        if kwargs:
            request_params.update(**kwargs)

        r = self._request('GET', self._build_url('activities'), params=request_params)

        if r.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve activities. Server responded with {}".format(str(r)))

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
              name=None,  # type: Optional[str]
              pk=None,  # type: Optional[str]
              model=None,  # type: Optional[Part]
              category=Category.INSTANCE,  # type: Optional[str]
              bucket=None,  # type: Optional[str]
              parent=None,  # type: Optional[str]
              activity=None,  # type: Optional[str]
              limit=None,  # type: Optional[int]
              batch=100,  # type: int
              **kwargs):
        # type: (...) -> PartSet
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
        # type: (*Any, **Any) -> Part
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
        # type: (*Any, **Any) -> Part
        """Retrieve single KE-chain part model.

        Uses the same interface as the `part` method but returns only a single pykechain `Part` instance.

        :return: a single :obj:`Part`
        :raises: NotFoundError, MultipleFoundError
        """
        kwargs['category'] = Category.MODEL
        _parts = self.parts(*args, **kwargs)

        if len(_parts) == 0:
            raise NotFoundError("No model fits criteria")
        if len(_parts) != 1:
            raise MultipleFoundError("Multiple model fit criteria")

        return _parts[0]

    def properties(self, name=None, pk=None, category=Category.INSTANCE):
        # type: (Optional[str], Optional[str], Optional[str]) -> List[Property]
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

        if r.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not create activity")

        data = r.json()

        return Activity(data['results'][0], client=self)

    def _create_part(self, action, data):
        r = self._request('POST', self._build_url('parts'),
                          params={"select_action": action},
                          data=data)

        if r.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not create part, {}: {}".format(str(r), r.content))

        return Part(r.json()['results'][0], client=self)

    def create_part(self, parent, model, name=None):
        """Create a new part instance from a given model under a given parent.

        :param parent: parent part instance
        :param model: target part model
        :param name: new part name
        :return: Part (category = instance)
        """
        if parent.category != Category.INSTANCE:
            raise APIError("The parent should be an instance")
        if model.category != Category.MODEL:
            raise APIError("The models should be of category 'MODEL'")

        if not name:
            name = model.name

        data = {
            "name": name,
            "parent": parent.id,
            "model": model.id
        }

        return self._create_part("new_instance", data)

    def create_model(self, parent, name, multiplicity='ZERO_MANY'):
        """Create a new child model under a given parent.

        :param parent: parent model
        :param name: new model name
        :param multiplicity: choose between ZERO_ONE, ONE, ZERO_MANY, ONE_MANY or M_N
        :return: Part (category = model)
        """
        if parent.category != Category.MODEL:
            raise APIError("The parent should be a model")

        data = {
            "name": name,
            "parent": parent.id,
            "multiplicity": multiplicity
        }

        return self._create_part("create_child_model", data)

    def create_proxy_model(self, model, parent, name, multiplicity='ZERO_MANY'):
        """Add this model as a proxy to another parent model.

        This will add a model as a proxy model to another parent model. It ensure that it will copy the
        whole subassembly to the 'parent' model.

        :param name: Name of the new proxy model
        :param parent: parent of the
        :param multiplicity: the multiplicity of the new proxy model (default ONE_MANY)
        :return: the new proxy model part
        """
        if model.category != Category.MODEL:
            raise IllegalArgumentError("The model should be of category MODEL")
        if parent.category != Category.MODEL:
            raise IllegalArgumentError("The parent should be of category MODEL")

        data = {
            "name": name,
            "model": model.id,
            "parent": parent.id,
            "multiplicity": multiplicity
        }

        return self._create_part('create_proxy_model', data)

    def create_property(self, model, name, description=None, property_type='CHAR', default_value=None):
        """Create a new property model under a given model.

        :param model: parent model
        :param name: property model name
        :param description: property model description (optional)
        :param property_type: choose between FLOAT, INT, TEXT, LINK, REFERENCE, DATETIME, BOOLEAN, CHAR, ATTACHMENT or
         SINGLE_SELECT
        :param default_value: default value used for part instances
        :return: Property
        """
        if model.category != Category.MODEL:
            raise IllegalArgumentError("The model should be of category MODEL")

        data = {
            "name": name,
            "part": model.id,
            "description": description,
            "property_type": property_type.upper() + '_VALUE',
            "value": default_value
        }

        r = self._request('POST', self._build_url('properties'),
                          data=data)

        if r.status_code != requests.codes.created:
            raise APIError("Could not create property")

        prop = Property.create(r.json()['results'][0], client=self)

        model.properties.append(prop)

        return prop
