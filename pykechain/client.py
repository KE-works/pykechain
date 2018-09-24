import warnings
from typing import Dict, Tuple, Optional, Any, List  # flake8: noqa

import requests
from envparse import env
from requests.compat import urljoin, urlparse  # type: ignore

from pykechain.enums import Category, KechainEnv, ScopeStatus, ActivityType, ServiceType, ServiceEnvironmentVersion, \
    WIMCompatibleActivityTypes, PropertyType
from pykechain.models.activity2 import Activity2
from pykechain.models.service import Service, ServiceExecution
from pykechain.models.user import User
from pykechain.utils import is_uuid
from .__about__ import version
from .exceptions import ForbiddenError, NotFoundError, MultipleFoundError, APIError, ClientError, IllegalArgumentError
from .models import Scope, Activity, Part, PartSet, Property

API_PATH = {
    'scopes': 'api/scopes.json',
    'scope': 'api/scopes/{scope_id}.json',
    'activities': 'api/activities.json',
    'activity': 'api/activities/{activity_id}.json',
    'activity_export': 'api/activities/{activity_id}/export',
    'parts': 'api/parts.json',
    'part': 'api/parts/{part_id}.json',
    'properties': 'api/properties.json',
    'property': 'api/properties/{property_id}.json',
    'property_upload': 'api/properties/{property_id}/upload',
    'property_download': 'api/properties/{property_id}/download',
    'widgets_config': 'api/widget_config.json',
    'widget_config': 'api/widget_config/{widget_config_id}.json',
    'services': 'api/services.json',
    'service': 'api/services/{service_id}.json',
    'service_execute': 'api/services/{service_id}/execute',
    'service_upload': 'api/services/{service_id}/upload',
    'service_download': 'api/services/{service_id}/download',
    'service_executions': 'api/service_executions.json',
    'service_execution': 'api/service_executions/{service_execution_id}.json',
    'service_execution_terminate': 'api/service_executions/{service_execution_id}/terminate',
    'service_execution_notebook_url': 'api/service_executions/{service_execution_id}/notebook_url',
    'service_execution_log': 'api/service_executions/{service_execution_id}/log',
    'users': 'api/users.json',
    'teams': 'api/teams.json',
    'team': 'api/teams/{team_id}.json',
    'versions': 'api/versions.json'
}

API_EXTRA_PARAMS = {
    'activity': {'fields': '__all__'},  # id,name,scope,status,classification,activity_type,parent_id'},
    'activities': {'fields': '__all__'}  # 'id,name,scope,status,classification,activity_type,parent_id'}
}


class Client(object):
    """The KE-chain 2 python client to connect to a KE-chain (version 2) instance.

    :ivar last_request: last executed request. Which is of type `requests.Request`_
    :ivar last_response: last executed response. Which is of type `requests.Response`_
    :ivar str last_url: last called api url
    :ivar app_versions: a list of the versions of the internal KE-chain 'app' modules

    .. _requests.Request: http://docs.python-requests.org/en/master/api/#requests.Request
    .. _requests.Response: http://docs.python-requests.org/en/master/api/#requests.Response
    """

    def __init__(self, url='http://localhost:8000/', check_certificates=True):
        # type: (str, bool) -> None
        """Create a KE-chain client with given settings.

        :param basestring url: the url of the KE-chain instance to connect to (defaults to http://localhost:8000)
        :param bool check_certificates: if to check TLS/SSL Certificates. Defaults to True

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
        self._app_versions = None  # type: Optional[List[dict]]

        if not check_certificates:
            self.session.verify = False

    def __repr__(self):  # pragma: no cover
        return "<pyke Client '{}'>".format(self.api_root)

    @classmethod
    def from_env(cls, env_filename=None):
        # type: (Optional[str]) -> Client
        """Create a client from environment variable settings.

        :param basestring env_filename: filename of the environment file, defaults to '.env' in the local dir
                                        (or parent dir)
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

        :param basestring username: username for your user from KE-chain
        :param basestring password: password for your user from KE-chain
        :param basestring token: user authentication token retrieved from KE-chain

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

        :return: list of dictionary with users information
        :rtype: list(dict)
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

    @property
    def app_versions(self):
        """List of the versions of the internal KE-chain 'app' modules."""
        if not self._app_versions:
            app_versions_url = self._build_url('versions')

            response = self._request('GET', app_versions_url)

            if response.status_code == requests.codes.not_found:
                self._app_versions = []
            elif response.status_code == requests.codes.forbidden:
                raise ForbiddenError(response.json()['results'][0]['detail'])
            elif response.status_code != requests.codes.ok:
                raise APIError("Could not retrieve app versions: {}".format(response))
            else:
                self._app_versions = response.json().get('results')

        return self._app_versions

    def match_app_version(self, app=None, label=None, version=None, default=False):
        """Match app version against a semantic version string.

        Checks if a KE-chain app matches a version comparison. Uses the `semver` matcher to check.

        `match("2.0.0", ">=1.0.0")` => `True`
        `match("1.0.0", ">1.0.0")` => `False`

        Examples
        --------
        >>> client.match_app_version(label='wim', version=">=1.99")
        >>> True

        >>> client.match_app_version(app='kechain2.core.pim', version=">=1.0.0")
        >>> True

        :param app: (optional) appname eg. 'kechain.core.wim'
        :type app: basestring or None
        :param label: (optional) app label (last part of the app name) eb 'wim'
        :type label: basestring or None
        :param version: semantic version string to match appname version against eg '2.0.0' or '>=2.0.0'
        :type version: basestring
        :param default: (optional) boolean to return if the version of the app is not set but the app found.
                        Set to None to return a NotFoundError when a version if not found in the app.
        :type default: bool or None
        :return: True if the version of the app matches against the match_version, otherwise False
        :raises IllegalArgumentError: if no app nor a label is provided
        :raises NotFoundError: if the app is not found
        :raises ValueError: if the version provided is not parseable by semver,
                            should contain (<operand><major>.<minor>.<patch) where <operand> is '>,<,>=,<=,=='

        """
        if not app or not label and not (app and label):
            target_app = [a for a in self.app_versions if a.get('app') == app or a.get('label') == label]
            if not target_app and not isinstance(default, bool):
                raise NotFoundError("Could not find the app or label provided")
            elif not target_app and isinstance(default, bool):
                return default
        else:
            raise IllegalArgumentError("Please provide either app or label")

        if not version:
            raise IllegalArgumentError("Please provide semantic version string including operand eg: `>=1.0.0`")

        app_version = target_app[0].get('version')

        if target_app and app_version and version:
            import semver
            return semver.match(app_version, version)
        elif not app_version:
            if isinstance(default, bool):
                return default
            else:
                raise NotFoundError("No version found on the app '{}'".format(target_app[0].get('app')))

    def reload(self, obj, extra_params=None):
        """Reload an object from server. This method is immutable and will return a new object.

        :param obj: object to reload
        :type obj: :py:obj:`obj`
        :param extra_params: additional object specific extra query string params (eg for activity)
        :type extra_params: dict
        :return: a new object
        :raises NotFoundError: if original object is not found or deleted in the mean time
        """
        if not obj._json_data.get('url'):  # pragma: no cover
            raise NotFoundError("Could not reload object, there is no url for object '{}' configured".format(obj))

        response = self._request('GET', obj._json_data.get('url'), params=extra_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not reload object ({})".format(response))

        data = response.json()

        return obj.__class__(data['results'][0], client=self)

    def scopes(self, name=None, pk=None, status=ScopeStatus.ACTIVE, **kwargs):
        # type: (Optional[str], Optional[str], Optional[str], **Any) -> List[Scope]
        """Return all scopes visible / accessible for the logged in user.

        If additional `keyword=value` arguments are provided, these are added to the request parameters. Please
        refer to the documentation of the KE-chain API for additional query parameters.

        :param name: if provided, filter the search for a scope/project by name
        :type name: basestring or None
        :param pk: if provided, filter the search by scope_id
        :type pk: basestring or None
        :param status: if provided, filter the search for the status. eg. 'ACTIVE', 'TEMPLATE', 'LIBRARY'
        :type status: basestring or None
        :param kwargs: optional additional search arguments
        :type kwargs: dict or None
        :return: list of `Scopes`
        :rtype: list(:class:`models.Scope`)
        :raises NotFoundError: if no scopes are not found.

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
        request_params = {
            'name': name,
            'id': pk,
            'status': status,
        }
        if kwargs:
            request_params.update(**kwargs)

        response = self._request('GET', self._build_url('scopes'), params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve scopes")

        data = response.json()

        return [Scope(s, client=self) for s in data['results']]

    def scope(self, *args, **kwargs):
        # type: (*Any, **Any) -> Scope
        """Return a single scope based on the provided name.

        If additional `keyword=value` arguments are provided, these are added to the request parameters. Please
        refer to the documentation of the KE-chain API for additional query parameters.

        :return: a single :class:`models.Scope`
        :raises NotFoundError: When no `Scope` is found
        :raises MultipleFoundError: When more than a single `Scope` is found
        """
        _scopes = self.scopes(*args, **kwargs)

        if len(_scopes) == 0:
            raise NotFoundError("No scope fits criteria")
        if len(_scopes) != 1:
            raise MultipleFoundError("Multiple scopes fit criteria")

        return _scopes[0]

    def activities(self, name=None, pk=None, scope=None, **kwargs):
        # type: (Optional[str], Optional[str], Optional[str], **Any) -> List[Activity]
        """Search for activities with optional name, pk and scope filter.

        If additional `keyword=value` arguments are provided, these are added to the request parameters. Please
        refer to the documentation of the KE-chain API for additional query parameters.

        :param pk: id (primary key) of the activity to retrieve
        :type pk: basestring or None
        :param name: filter the activities by name
        :type name: basestring or None
        :param scope: filter by scope id
        :type scope: basestring or None
        :return: list of :class:`models.Activity`
        :raises NotFoundError: If no `Activities` are found
        """
        request_params = {
            'id': pk,
            'name': name,
            'scope': scope
        }

        # update the fields query params
        # for 'kechain.core.wim >= 2.0.0' add additional API params
        if self.match_app_version(label='wim', version='>=2.0.0', default=False):
            request_params.update(API_EXTRA_PARAMS['activity'])

        if kwargs:
            request_params.update(**kwargs)

        response = self._request('GET', self._build_url('activities'), params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve activities. Server responded with {}".format(str(response)))

        data = response.json()

        # for 'kechain.core.wim >= 2.0.0' we return Activity2, otherwise Activity1
        if self.match_app_version(label='wim', version='<2.0.0', default=True):
            # WIM1
            return [Activity(a, client=self) for a in data['results']]
        else:
            # WIM2
            return [Activity2(a, client=self) for a in data['results']]

    def activity(self, *args, **kwargs):
        # type: (*Any, **Any) -> Activity
        """Search for a single activity.

        If additional `keyword=value` arguments are provided, these are added to the request parameters. Please
        refer to the documentation of the KE-chain API for additional query parameters.

        :param pk: id (primary key) of the activity to retrieve
        :type pk: basestring or None
        :param name: filter the activities by name
        :type name: basestring or None
        :param scope: filter by scope id
        :type scope: basestring or None
        :return: a single :class:`models.Activity`
        :raises NotFoundError: When no `Activity` is found
        :raises MultipleFoundError: When more than a single `Activity` is found
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

        If no parameters are provided, all parts are retrieved.

        If additional `keyword=value` arguments are provided, these are added to the request parameters. Please
        refer to the documentation of the KE-chain API for additional query parameters.

        :param name: filter on name
        :type name: basestring or None
        :param pk: filter on primary key
        :type pk: basestring or None
        :param model: filter on model_id
        :type model: basestring or None
        :param category: filter on category (INSTANCE, MODEL, None)
        :type category: basestring or None
        :param bucket: filter on bucket_id
        :type bucket: basestring or None
        :param parent: filter on the parent_id, returns all childrent of the parent_id
        :type parent: basestring or None
        :param activity: filter on activity_id
        :type activity: basestring or None
        :param limit: limit the return to # items (default unlimited, so return all results)
        :type limit: int or None
        :param batch: limit the batch size to # items (defaults to 100 items per batch)
        :type batch: int or None
        :param kwargs: additional `keyword=value` arguments for the api
        :type kwargs: dict or None
        :return: :class:`models.PartSet` which is an iterator of :class:`models.Part`
        :raises NotFoundError: If no `Part` is found

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

        response = self._request('GET', self._build_url('parts'), params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve parts")

        data = response.json()

        part_results = data['results']

        if batch and data.get('next'):
            while data['next']:
                # respect the limit if set to > 0
                if limit and len(part_results) >= limit:
                    break
                response = self._request('GET', data['next'])
                data = response.json()
                part_results.extend(data['results'])

        return PartSet((Part(p, client=self) for p in part_results))

    def part(self, *args, **kwargs):
        # type: (*Any, **Any) -> Part
        """Retrieve single KE-chain part.

        Uses the same interface as the :func:`parts` method but returns only a single pykechain :class:`models.Part`
        instance.

        If additional `keyword=value` arguments are provided, these are added to the request parameters. Please
        refer to the documentation of the KE-chain API for additional query parameters.

        :return: a single :class:`models.Part`
        :raises NotFoundError: When no `Part` is found
        :raises MultipleFoundError: When more than a single `Part` is found
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

        Uses the same interface as the :func:`part` method but returns only a single pykechain
        :class:`models.Part` instance of category `MODEL`.

        If additional `keyword=value` arguments are provided, these are added to the request parameters. Please
        refer to the documentation of the KE-chain API for additional query parameters.

        :return: a single :class:`models.Part`
        :raises NotFoundError: When no `Part` is found
        :raises MultipleFoundError: When more than a single `Part` is found
        """
        kwargs['category'] = Category.MODEL
        _parts = self.parts(*args, **kwargs)

        if len(_parts) == 0:
            raise NotFoundError("No model fits criteria")
        if len(_parts) != 1:
            raise MultipleFoundError("Multiple models fit criteria")

        return _parts[0]

    def property(self, *args, **kwargs):
        # type: (*Any, **Any) -> Property
        """Retrieve single KE-chain Property.

        Uses the same interface as the :func:`properties` method but returns only a single pykechain :class:
        `models.Property` instance.

        If additional `keyword=value` arguments are provided, these are added to the request parameters. Please
        refer to the documentation of the KE-chain API for additional query parameters.

        :return: a single :class:`models.Property`
        :raises NotFoundError: When no `Property` is found
        :raises MultipleFoundError: When more than a single `Property` is found
        """
        _properties = self.properties(*args, **kwargs)

        if len(_properties) == 0:
            raise NotFoundError("No property fits criteria")
        if len(_properties) != 1:
            raise MultipleFoundError("Multiple properties fit criteria")

        return _properties[0]

    def properties(self, name=None, pk=None, category=Category.INSTANCE, **kwargs):
        # type: (Optional[str], Optional[str], Optional[str], **Any) -> List[Property]
        """Retrieve properties.

        If additional `keyword=value` arguments are provided, these are added to the request parameters. Please
        refer to the documentation of the KE-chain API for additional query parameters.

        :param name: name to limit the search for.
        :type name: basestring or None
        :param pk: primary key or id (UUID) of the property to search for
        :type pk: basestring or None
        :param category: filter the properties by category. Defaults to INSTANCE. Other options MODEL or None
        :type category: basestring or None
        :param kwargs: (optional) additional search keyword arguments
        :type kwargs: dict or None
        :return: list of :class:`models.Property`
        :raises NotFoundError: When no `Property` is found
        """
        request_params = {
            'name': name,
            'id': pk,
            'category': category
        }
        if kwargs:
            request_params.update(**kwargs)

        response = self._request('GET', self._build_url('properties'), params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve properties")

        data = response.json()

        return [Property.create(p, client=self) for p in data['results']]

    def services(self, name=None, pk=None, scope=None, **kwargs):
        """
        Retrieve Services.

        If additional `keyword=value` arguments are provided, these are added to the request parameters. Please
        refer to the documentation of the KE-chain API for additional query parameters.

        :param name: (optional) name to limit the search for
        :type name: basestring or None
        :param pk: (optional) primary key or id (UUID) of the service to search for
        :type pk: basestring or None
        :param scope: (optional) id (UUID) of the scope to search in
        :type scope: basestring or None
        :param kwargs: (optional) additional search keyword arguments
        :type kwargs: dict or None
        :return: list of :class:`models.Service` objects
        :raises NotFoundError: When no `Service` objects are found
        """
        request_params = {
            'name': name,
            'id': pk,
            'scope': scope
        }
        if kwargs:
            request_params.update(**kwargs)

        response = self._request('GET', self._build_url('services'), params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve services")

        data = response.json()
        return [Service(service, client=self) for service in data['results']]

    def service(self, name=None, pk=None, scope=None, **kwargs):
        """
        Retrieve single KE-chain Service.

        Uses the same interface as the :func:`services` method but returns only a single pykechain
        :class:`models.Service` instance.

        :param name: (optional) name to limit the search for
        :type name: basestring or None
        :param pk: (optional) primary key or id (UUID) of the service to search for
        :type pk: basestring or None
        :param scope: (optional) id (UUID) of the scope to search in
        :type scope: basestring or None
        :param kwargs: (optional) additional search keyword arguments
        :type kwargs: dict or None
        :return: a single :class:`models.Service` object
        :raises NotFoundError: When no `Service` object is found
        :raises MultipleFoundError: When more than a single `Service` object is found
        """
        _services = self.services(name=name, pk=pk, scope=scope, **kwargs)

        if len(_services) == 0:
            raise NotFoundError("No service fits criteria")
        if len(_services) != 1:
            raise MultipleFoundError("Multiple services fit criteria")

        return _services[0]

    def service_executions(self, name=None, pk=None, scope=None, service=None, **kwargs):
        """
        Retrieve Service Executions.

        If additional `keyword=value` arguments are provided, these are added to the request parameters. Please
        refer to the documentation of the KE-chain API for additional query parameters.

        :param name: (optional) name to limit the search for
        :type name: basestring or None
        :param pk: (optional) primary key or id (UUID) of the service to search for
        :type pk: basestring or None
        :param scope: (optional) id (UUID) of the scope to search in
        :type scope: basestring or None
        :param service: (optional) service UUID to filter on
        :type service: basestring or None
        :param kwargs: (optional) additional search keyword arguments
        :type kwargs: dict or None
        :return: a single :class:`models.ServiceExecution` object
        :raises NotFoundError: When no `ServiceExecution` object is found
        """
        request_params = {
            'name': name,
            'id': pk,
            'service': service,
            'scope': scope
        }
        if kwargs:
            request_params.update(**kwargs)

        r = self._request('GET', self._build_url('service_executions'), params=request_params)

        if r.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve service executions")

        data = r.json()
        return [ServiceExecution(service_exeuction, client=self) for service_exeuction in data['results']]

    def service_execution(self, name=None, pk=None, scope=None, service=None, **kwargs):
        """
        Retrieve single KE-chain ServiceExecution.

        Uses the same interface as the :func:`service_executions` method but returns only a single
        pykechain :class:`models.ServiceExecution` instance.

        If additional `keyword=value` arguments are provided, these are added to the request parameters. Please
        refer to the documentation of the KE-chain API for additional query parameters.

        :param name: (optional) name to limit the search for
        :type name: basestring or None
        :param pk: (optional) primary key or id (UUID) of the service to search for
        :type pk: basestring or None
        :param scope: (optional) id (UUID) of the scope to search in
        :type scope: basestring or None
        :param kwargs: (optional) additional search keyword arguments
        :type kwargs: dict or None
        :return: a single :class:`models.ServiceExecution` object
        :raises NotFoundError: When no `ServiceExecution` object is found
        :raises MultipleFoundError: When more than a single `ServiceExecution` object is found
        """
        _service_executions = self.service_executions(name=name, pk=pk, scope=scope, service=service, **kwargs)

        if len(_service_executions) == 0:
            raise NotFoundError("No service execution fits criteria")
        if len(_service_executions) != 1:
            raise MultipleFoundError("Multiple service executions fit criteria")

        return _service_executions[0]

    def users(self, username=None, pk=None, **kwargs):
        """
        Users of KE-chain.

        Provide a list of :class:`User`s of KE-chain. You can filter on username or id or any other advanced filter.

        :param username: (optional) username to filter
        :type username: basestring or None
        :param pk: (optional) id of the user to filter
        :type pk: basestring or None
        :param kwargs: Additional filtering keyword=value arguments
        :type kwargs: dict or None
        :return: List of :class:`Users`
        :raises NotFoundError: when a user could not be found
        """
        request_params = {
            'username': username,
            'pk': pk,
        }
        if kwargs:
            request_params.update(**kwargs)

        r = self._request('GET', self._build_url('users'), params=request_params)

        if r.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not find users: '{}'".format(r.json()))

        data = r.json()
        return [User(user, client=self) for user in data['results']]

    def user(self, username=None, pk=None, **kwargs):
        """
        User of KE-chain.

        Provides single user of :class:`User` of KE-chain. You can filter on username or id or an advanced filter.

        :param username: (optional) username to filter
        :type username: basestring or None
        :param pk: (optional) id of the user to filter
        :type pk: basestring or None
        :param kwargs: Additional filtering keyword=value arguments
        :type kwargs: dict or None
        :return: List of :class:`User`
        :raises NotFoundError: when a user could not be found
        :raises MultipleFoundError: when more than a single user can be found
        """
        _users = self.users(username=username, pk=pk, **kwargs)

        if len(_users) == 0:
            raise NotFoundError("No user criteria")
        if len(_users) != 1:
            raise MultipleFoundError("Multiple users fit criteria")

        return _users[0]

    #
    # Creators
    #

    def create_activity(self, *args, **kwargs):
        """
        Create a new activity.

        .. important::
            This is a shim function that based on the implementation of KE-chain will determine to create
            the activity using the legacy WIM API (KE-chain < 2.9.0) or the newer WIM2 API (KE-chain >= 2.9.0).
            It will either return a :class:`Activity` or a :class:`Activity2`.

        :param args:
        :param kwargs:
        :return: the created :class:`models.Activity` or :class:`models.Activity2`
        :raises APIError: When the object could not be created
        :raises IllegalArgumentError: When the provided arguments are incompatible with the WIM API implementation.
        """
        if self.match_app_version(label='wim', version='<2.0.0', default=True):
            # for wim1
            if 'activity_type' in kwargs:
                warnings.warn('For WIM versions 1, you need to ensure to use `activity_class`. Update your code; '
                              'This will be deprecated in APR2018.')
                activity_type = kwargs.pop('activity_type')
                if activity_type not in ActivityType.values():
                    raise IllegalArgumentError(
                        "Please provide accepted activity_type: '{}' not allowed".format(activity_type))
                kwargs['activity_class'] = WIMCompatibleActivityTypes.get(activity_type)
            if 'parent' in kwargs:
                warnings.warn('For WIM versions 1, you need to ensure to use `process`. Update your code; '
                              'This will be deprecated in APR2018.')
                kwargs['process'] = kwargs.pop('parent')
            return self._create_activity1(*args, **kwargs)
        else:
            # for wim2
            # make old calls compatible with WIM2
            if 'activity_class' in kwargs:
                warnings.warn('For WIM versions 2, you need to ensure to use `activity_type`. Update your code; '
                              'This will be deprecated in APR2018.')
                activity_class = kwargs.pop('activity_class')
                if activity_class not in ActivityType.values():
                    raise IllegalArgumentError(
                        "Please provide accepted activity_type: '{}' not allowed".format(activity_class))
                kwargs['activity_type'] = WIMCompatibleActivityTypes.get(activity_class)
            if 'process' in kwargs:
                warnings.warn('For WIM versions 2, you need to ensure to use `parent` instead of `process`. Update '
                              'your code; This will be deprecated in APR2018.')
                kwargs['parent'] = kwargs.pop('process')
            return self._create_activity2(*args, **kwargs)

    # WIM1
    def _create_activity1(self, process, name, activity_class="UserTask"):
        """Create a new activity.

        :param process: parent process id
        :type process: basestring
        :param name: new activity name
        :type name: basestring
        :param activity_class: type of activity: UserTask (default) or Subprocess
        :type activity_class: basestring
        :return: the created :class:`models.Activity`
        :raises IllegalArgumentError: When the provided arguments are incorrect
        :raises APIError: When the object could not be created
        """
        if self.match_app_version(label='wim', version='>=2.0.0', default=False):
            raise APIError('This method is only compatible with versions of KE-chain where the internal `wim` module '
                           'has a version <=2.0.0. Use the `Client.create_activity2()` method.')

        if activity_class and activity_class not in ActivityType.values():
            raise IllegalArgumentError(
                "Please provide accepted activity_class (provided:{} accepted:{})".format(
                    activity_class, (ActivityType.USERTASK, ActivityType.SUBPROCESS, ActivityType.SERVICETASK)))
        data = {
            "name": name,
            "process": process,
            "activity_class": activity_class
        }

        response = self._request('POST', self._build_url('activities'), data=data)

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not create activity")

        data = response.json()

        return Activity(data['results'][0], client=self)

    # WIM2
    def _create_activity2(self, parent, name, activity_type=ActivityType.TASK):
        """Create a new activity.

        .. important::
            This function creates activities for KE-chain versions later than 2.9.0-135
            In effect where the module 'wim' has version '>=2.0.0'.
            The version of 'wim' in KE-chain can be found in the property :attr:`Client.app_versions`

        In WIM2 the type of the activity is called activity_type

        :param parent: parent under which to create the activity
        :type parent: basestring or :class:`models.Activity2`
        :param name: new activity name
        :type name: basestring
        :param activity_type: type of activity: TASK (default) or PROCESS
        :type activity_type: basestring
        :return: the created :class:`models.Activity2`
        :raises APIError: When the object could not be created
        :raises IllegalArgumentError: When an incorrect activitytype or parent is provided
        """
        # WIM1: activity_class, WIM2: activity_type
        if self.match_app_version(label='wim', version='<2.0.0', default=True):
            raise APIError('This method is only compatible with versions of KE-chain where the internal `wim` module '
                           'has a version >=2.0.0. Use the `Client.create_activity()` method.')

        if activity_type and activity_type not in ActivityType.values():
            raise IllegalArgumentError("Please provide accepted activity_type (provided:{} accepted:{})".
                                       format(activity_type, ActivityType.values()))
        if isinstance(parent, (Activity, Activity2)):
            parent = parent.id
        elif is_uuid(parent):
            parent = parent
        else:
            raise IllegalArgumentError("Please provide either an activity object or a UUID")

        data = {
            "name": name,
            "parent_id": parent,
            "activity_type": activity_type
        }

        response = self._request('POST', self._build_url('activities'), data=data,
                                 params=API_EXTRA_PARAMS['activities'])

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not create activity")

        data = response.json()

        return Activity2(data['results'][0], client=self)

    def _create_part(self, action, data, **kwargs):
        """Create a part internal core function."""
        # suppress_kevents should be in the data (not the query_params)
        if 'suppress_kevents' in kwargs:
            data['suppress_kevents'] = kwargs.pop('suppress_kevents')

        # prepare url query parameters
        query_params = kwargs
        query_params['select_action'] = action

        response = self._request('POST', self._build_url('parts'),
                                 params=query_params,  # {"select_action": action},
                                 data=data)

        if response.status_code != requests.codes.created:
            raise APIError("Could not create part, {}: {}".format(str(response), response.content))

        return Part(response.json()['results'][0], client=self)

    def create_part(self, parent, model, name=None, **kwargs):
        """Create a new part instance from a given model under a given parent.

        In order to prevent the backend from updating the frontend you may add `suppress_kevents=True` as
        additional keyword=value argument to this method. This will improve performance of the backend
        against a trade-off that someone looking at the frontend won't notice any changes unless the page
        is refreshed.

        :param parent: parent part instance of the new instance
        :type parent: :class:`models.Part`
        :param model: target part model on which the new instance is based
        :type model: :class:`models.Part`
        :param name: new part name
        :type name: basestring
        :param kwargs: (optional) additional keyword=value arguments
        :return: Part (category = instance)
        :return: :class:`models.Part` with category `INSTANCE`
        :raises IllegalArgumentError: When the provided arguments are incorrect
        :raises APIError: if the `Part` could not be created
        """
        if parent.category != Category.INSTANCE:
            raise IllegalArgumentError("The parent should be an category 'INSTANCE'")
        if model.category != Category.MODEL:
            raise IllegalArgumentError("The models should be of category 'MODEL'")

        if not name:
            name = model.name

        data = {
            "name": name,
            "parent": parent.id,
            "model": model.id
        }

        return self._create_part(action="new_instance", data=data, **kwargs)

    def create_model(self, parent, name, multiplicity='ZERO_MANY', **kwargs):
        """Create a new child model under a given parent.

        In order to prevent the backend from updating the frontend you may add `suppress_kevents=True` as
        additional keyword=value argument to this method. This will improve performance of the backend
        against a trade-off that someone looking at the frontend won't notice any changes unless the page
        is refreshed.

        :param parent: parent model
        :param name: new model name
        :param parent: parent part instance
        :type parent: :class:`models.Part`
        :param name: new part name
        :type name: basestring
        :param multiplicity: choose between ZERO_ONE, ONE, ZERO_MANY, ONE_MANY or M_N
        :type multiplicity: basestring
        :param kwargs: (optional) additional keyword=value arguments
        :type kwargs: dict
        :return: :class:`models.Part` with category `MODEL`
        :raises IllegalArgumentError: When the provided arguments are incorrect
        :raises APIError: if the `Part` could not be created
        """
        if parent.category != Category.MODEL:
            raise IllegalArgumentError("The parent should be of category 'MODEL'")

        data = {
            "name": name,
            "parent": parent.id,
            "multiplicity": multiplicity
        }

        return self._create_part(action="create_child_model", data=data, **kwargs)

    def _create_clone(self, parent, part, **kwargs):
        """Create a new `Part` clone under the `Parent`.

        .. versionadded:: 2.3

        :param parent: parent part
        :type parent: :class:`models.Part`
        :param part: part to be cloned
        :type part: :class:`models.Part`
        :param kwargs: (optional) additional keyword=value arguments
        :type kwargs: dict
        :return: cloned :class:`models.Part`
        :raises APIError: if the `Part` could not be cloned
        """
        if part.category == Category.MODEL:
            select_action = 'clone_model'
        else:
            select_action = 'clone_instance'

        data = {
            "part": part.id,
            "parent": parent.id,
            "suppress_kevents": kwargs.pop('suppress_kevents', None)
        }

        # prepare url query parameters
        query_params = kwargs
        query_params['select_action'] = select_action

        response = self._request('POST', self._build_url('parts'),
                                 params=query_params,
                                 data=data)

        if response.status_code != requests.codes.created:
            raise APIError("Could not clone part, {}: {}".format(str(response), response.content))

        return Part(response.json()['results'][0], client=self)

    def create_proxy_model(self, model, parent, name, multiplicity='ZERO_MANY', **kwargs):
        """Add this model as a proxy to another parent model.

        This will add a model as a proxy model to another parent model. It ensure that it will copy the
        whole sub-assembly to the 'parent' model.

        In order to prevent the backend from updating the frontend you may add `suppress_kevents=True` as
        additional keyword=value argument to this method. This will improve performance of the backend
        against a trade-off that someone looking at the frontend won't notice any changes unless the page
        is refreshed.

        :param model: the catalog proxy model the new proxied model should be based upon
        :type model: :class:`models.Part`
        :param parent: parent part instance
        :type parent: :class:`models.Part`
        :param name: new part name
        :type name: basestring
        :param multiplicity: choose between ZERO_ONE, ONE, ZERO_MANY, ONE_MANY or M_N, default is `ZERO_MANY`
        :type multiplicity: basestring
        :param kwargs: (optional) additional keyword=value arguments
        :type kwargs: dict
        :return: the new proxy :class:`models.Part` with category `MODEL`
        :raises IllegalArgumentError: When the provided arguments are incorrect
        :raises APIError: if the `Part` could not be created
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

        return self._create_part(action='create_proxy_model', data=data, **kwargs)

    def create_property(self, model, name, description=None, property_type=PropertyType.CHAR_VALUE, default_value=None,
                        unit=None, options=None):
        """Create a new property model under a given model.

        Use the :class:`enums.PropertyType` to select which property type to create to ensure that you
        provide the correct values to the KE-chain backend. The default is a `PropertyType.CHAR_VALUE` which is a
        single line text in KE-chain.


        :param model: parent model
        :type model: :class:`models.Part`
        :param name: property model name
        :type name: basestring
        :param description: property model description (optional)
        :type description: basestring or None
        :param property_type: choose one of the :class:`enums.PropertyType`, defaults to `PropertyType.CHAR_VALUE`.
        :type property_type: basestring or None
        :param default_value: (optional) default value used for part instances when creating a model.
        :type default_value: any
        :param unit: (optional) unit of the property
        :type unit: basestring or None
        :param options: (optional) property options (eg. validators or 'single selectlist choices')
        :type options: basestring or None
        :return: a :class:`models.Property` with category `MODEL`
        :raises IllegalArgumentError: When the provided arguments are incorrect
        :raises APIError: if the `Property` model could not be created
        """
        if model.category != Category.MODEL:
            raise IllegalArgumentError("The model should be of category MODEL")

        if not property_type.endswith('_VALUE'):
            warnings.warn("Please use the `PropertyType` enumeration to ensure providing correct "
                          "values to the backend.", UserWarning)
            property_type = '{}_VALUE'.format(property_type.upper())

        if property_type not in PropertyType.values():
            raise IllegalArgumentError("Please provide a valid propertytype, please use one of `enums.PropertyType`. "
                                       "Got: '{}'".format(property_type))

        # because the references value only accepts a single 'model_id' in the default value, we need to convert this
        # to a single value from the list of values.
        if property_type in (PropertyType.REFERENCE_VALUE, PropertyType.REFERENCES_VALUE) and \
                isinstance(default_value, (list, tuple)) and default_value:
            default_value = default_value[0]

        data = {
            "name": name,
            "part": model.id,
            "description": description or '',
            "property_type": property_type.upper(),
            "value": default_value,
            "unit": unit or '',
            "options": options or {}
        }

        # # We add options after the fact only if they are available, otherwise the options will be set to null in the
        # # request and that can't be handled by KE-chain.
        # if options:
        #     data['options'] = options

        response = self._request('POST', self._build_url('properties'),
                                     json=data)

        if response.status_code != requests.codes.created:
            raise APIError("Could not create property")

        prop = Property.create(response.json()['results'][0], client=self)

        model.properties.append(prop)

        return prop

    def create_service(self, name, scope, description=None, version=None,
                       service_type=ServiceType.PYTHON_SCRIPT,
                       environment_version=ServiceEnvironmentVersion.PYTHON_3_5,
                       pkg_path=None):
        """
        Create a Service.

        A service can be created only providing the name (and scope). Other information can be added later.
        If you provide a path to the `kecpkg` (or python script) to upload (`pkg_path`) on creation,
        this `kecpkg` will be uploaded in one go. If the later fails, the service is still there, and the package is
        not uploaded.

        :param name: Name of the service
        :type name: basestring
        :param scope: Scope where the create the Service under
        :type scope: :class:`models.Scope`
        :param description: (optional) description of the Service
        :type description: basestring or None
        :param version: (optional) version information of the Service
        :type version: basestring or None
        :param service_type: (optional) service type of the service (refer to :class:`pykechain.enums.ServiceType`),
                             defaults to `PYTHON_SCRIPT`
        :type service_type: basestring or None
        :param environment_version: (optional) execution environment of the service (refer to
         :class:`pykechain.enums.ServiceEnvironmentVersion`), defaults to `PYTHON_3_5`
        :type environment_version: basestring or None
        :param pkg_path: (optional) full path name to the `kecpkg` (or python script) to upload
        :type pkg_path: basestring or None
        :return: the created :class:`models.Service`
        :raises IllegalArgumentError: When the provided arguments are incorrect
        :raises APIError: In case of failure of the creation or failure to upload the pkg_path
        :raises OSError: In case of failure to locate the `pkg_path`
        """
        if service_type not in ServiceType.values():
            raise IllegalArgumentError("The type should be of one of {}".format(ServiceType.values()))

        if environment_version not in ServiceEnvironmentVersion.values():
            raise IllegalArgumentError("The environment version should be of one of {}".
                                       format(ServiceEnvironmentVersion.values()))

        data = {
            "name": name,
            "scope": scope,
            "description": description,
            "script_type": service_type,
            "script_version": version,
            "env_version": environment_version,
        }

        response = self._request('POST', self._build_url('services'),
                                 data=data)

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not create service ({})".format((response, response.json())))

        service = Service(response.json().get('results')[0], client=self)

        if pkg_path:
            # upload the package
            service.upload(pkg_path)

        # refresh service contents in place
        service.refresh()

        return service
