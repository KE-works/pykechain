import datetime
import warnings
from typing import Dict, Tuple, Optional, Any, List  # noqa: F401 pragma: no cover

import requests
from envparse import env
from requests.compat import urljoin, urlparse  # type: ignore
from six import text_type, string_types

from pykechain.enums import Category, KechainEnv, ScopeStatus, ActivityType, ServiceType, ServiceEnvironmentVersion, \
    WIMCompatibleActivityTypes, PropertyType, TeamRoles, Multiplicity
from pykechain.models import Part2, Property2
from pykechain.models.activity2 import Activity2
from pykechain.models.scope2 import Scope2
from pykechain.models.service import Service, ServiceExecution
from pykechain.models.team import Team
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
    'team_add_members': 'api/teams/{team_id}/add_members',
    'team_remove_members': 'api/teams/{team_id}/remove_members',
    'versions': 'api/versions.json',

    # PIM2
    'scope2': 'api/v2/scopes/{scope_id}.json',
    'scope2_add_member': 'api/v2/scopes/{scope_id}/add_member',
    'scope2_remove_member': 'api/v2/scopes/{scope_id}/remove_member',
    'scope2_add_manager': 'api/v2/scopes/{scope_id}/add_manager',
    'scope2_remove_manager': 'api/v2/scopes/{scope_id}/remove_manager',
    'scopes2': 'api/v2/scopes.json',
    'scopes2_clone': 'api/v2/scopes/clone',
    'parts2': 'api/v2/parts.json',
    'parts2_new_instance': 'api/v2/parts/new_instance',
    'parts2_create_child_model': 'api/v2/parts/create_child_model',
    'parts2_create_proxy_model': 'api/v2/parts/create_proxy_model',
    'parts2_clone_model': 'api/v2/parts/clone_model',
    'parts2_clone_instance': 'api/v2/parts/clone_instance',
    'parts2_export': 'api/v2/parts/export',
    'part2': 'api/v2/parts/{part_id}.json',
    'properties2': 'api/v2/properties.json',
    'properties2_create_model': 'api/v2/properties/create_model',
    'property2': 'api/v2/properties/{property_id}.json',
    'property2_upload': 'api/v2/properties/{property_id}/upload',
    'property2_download': 'api/v2/properties/{property_id}/download',
}

API_QUERY_PARAM_ALL_FIELDS = {'fields': '__all__'}
PARAMS_BASE = ["id", "name"]

API_EXTRA_PARAMS = {
    'activity': {
        'fields': ['id', 'name', 'activity_type', 'progress', 'assignees_names', 'start_date', 'due_date', 'status',
                   'parent_id', 'scope_id', 'parent_id_name', 'customization']
    },
    'activities': {
        'fields': ['id', 'name', 'activity_type', 'progress', 'assignees_names', 'start_date', 'due_date', 'status',
                   'parent_id', 'scope_id', 'parent_id_name', 'customization']
    },
    'scope2': {'fields': ",".join(
        ['id', 'name', 'text', 'start_date', 'due_date', 'status', 'progress', 'members', 'team', 'tags',
         'scope_options', 'team_id_name'])},
    'scopes2': {'fields': ",".join(
        ['id', 'name', 'text', 'start_date', 'due_date', 'status', 'progress', 'members', 'team', 'tags',
         'scope_options', 'team_id_name'])},
    'part2': {'fields': ",".join(
        ['id', 'name', 'properties', 'category', 'classification', 'parent_id', 'multiplicity', 'value_options',
         'property_type', 'value', 'order', 'part_id', 'scope_id', 'model_id', 'proxy_source_id_name'])},
    'parts2': {'fields': ",".join(
        ['id', 'name', 'properties', 'category', 'classification', 'parent_id', 'multiplicity', 'value_options',
         'property_type', 'value', 'order', 'part_id', 'scope_id', 'model_id', 'proxy_source_id_name'])},
    'properties2': {'fields': ",".join(
        ['id', 'name', 'model_id', 'part_id', 'order', 'scope_id', 'category', 'property_type', 'value',
         'value_options', 'description', 'unit'])},
    'property2': {'fields': ",".join(
        ['id', 'name', 'model_id', 'part_id', 'order', 'scope_id', 'category', 'property_type', 'value',
         'value_options', 'description', 'unit'])}
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

    def reload(self, obj, url=None, extra_params=None):
        """Reload an object from server. The original object is immutable and it will return a new object.

        The object will be refetched from KE-chain. If the object has a 'url' field the url will be taken from
        that field (KE-chain version 2). If the object does not have an 'url' field it will be constructed based
        on the class name and the id of the object itself. If `extra_params` are provided, these will be respected.
        If additional API params are needed to be included (eg. for KE-chain 3/PIM2) these will be added/updated
        automatically before the request continues.

        :param obj: object to reload
        :type obj: :py:obj:`obj`
        :param url: (optional) url to use
        :type url: basestring or None
        :param extra_params: additional object specific extra query string params (eg for activity)
        :type extra_params: dict
        :return: a new object
        :raises NotFoundError: if original object is not found or deleted in the mean time
        """
        if not url and not obj._json_data.get('url'):
            # build the url from the class name (in lower case) `obj.__class__.__name__.lower()`
            # get the id from the `obj.id` which is normally a keyname `<class_name>_id` (without the '2' if so)

            url = self._build_url(obj.__class__.__name__.lower(),
                                  **{"{}_id".format(obj.__class__.__name__.lower().replace("2", "")): obj.id})
            extra_api_params = API_EXTRA_PARAMS.get(obj.__class__.__name__.lower())
            # add the additional API params to the already provided extra params if they are provided.
            extra_params = extra_params.update(**extra_api_params) if extra_params else extra_api_params
        elif url:
            url = url
        else:
            url = obj._json_data.get('url')

        response = self._request('GET', url, params=extra_params)

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

        if self.match_app_version(label='gscope', version='>=2.0.0', default=False):
            request_params.update(API_EXTRA_PARAMS['scope2'])
            url = self._build_url('scopes2')
        else:
            url = self._build_url('scopes')

        if kwargs:
            request_params.update(**kwargs)

        response = self._request('GET', url=url, params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve scopes: '{}'".format(response.content))

        data = response.json()

        # for 'kechain.gcore.gscope >= 2.0.0 we return Scope2 otherwiser Scope
        if self.match_app_version(label='gscope', version='>=2.0.0', default=False):
            # Scope2
            return [Scope2(s, client=self) for s in data['results']]
        else:
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
              scope_id=None,  # type: Optional[str]
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
        :param bucket: filter on bucket_id  # only relevant for KE-chain 2
        :type bucket: basestring or None
        :param scope_id: filter on scope_id # relevant for KE-chain 2 and 3
        :type scope_id: basestring or None
        :param parent: filter on the parent_id, returns all children of the parent_id
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

        request_params = dict(
            id=pk,
            name=name,
            category=category,
            activity_id=activity,
            limit=batch,
            scope_id=scope_id
        )

        if self.match_app_version(label='gpim', version='>=2.0.0'):
            request_params.update(dict(
                parent_id=parent,
                model_id=model.id if model else None,
            ))
            url = self._build_url('parts2')
            request_params.update(API_EXTRA_PARAMS['parts2'])
        else:
            request_params.update(dict(
                bucket=bucket,
                parent=parent,
                model=model.id if model else None
            ))
            url = self._build_url('parts')

        if kwargs:
            request_params.update(**kwargs)

        response = self._request('GET', url, params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve parts: {}".format(response.content))

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

        if self.match_app_version(label='gpim', version='>=2.0.0'):
            return PartSet((Part2(p, client=self) for p in part_results))
        else:
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

        if self.match_app_version(label='gpim', version='>=2.0.0'):
            request_params.update(API_EXTRA_PARAMS['properties2'])
            response = self._request('GET', self._build_url('properties2'), params=request_params)
        else:
            response = self._request('GET', self._build_url('properties'), params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve properties: '{}'".format(response.content))

        data = response.json()

        if self.match_app_version(label='gpim', version='>=2.0.0'):
            return [Property2.create(p, client=self) for p in data['results']]
        else:
            return [Property.create(p, client=self) for p in data['results']]

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

        response = self._request('GET', self._build_url('service_executions'), params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve service executions")

        data = response.json()
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

        response = self._request('GET', self._build_url('users'), params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not find users: '{}'".format(response.json()))

        data = response.json()
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
            raise NotFoundError("No user criteria matches")
        if len(_users) != 1:
            raise MultipleFoundError("Multiple users fit criteria")

        return _users[0]

    def team(self, name=None, pk=None, is_hidden=False, **kwargs):
        """
        Team of KE-chain.

        Provides a team of :class:`Team` of KE-chain. You can filter on team name or provide id.

        :param name: (optional) team name to filter
        :type name: basestring or None
        :param pk: (optional) id of the user to filter
        :type pk: basestring or None
        :param is_hidden: (optional) boolean to show non-hidden or hidden teams or both (None) (default is non-hidden)
        :type is_hidden: bool or None
        :param kwargs: Additional filtering keyword=value arguments
        :type kwargs: dict or None
        :return: List of :class:`Team`
        :raises NotFoundError: when a user could not be found
        :raises MultipleFoundError: when more than a single user can be found
        """
        _teams = self.teams(name=name, pk=pk, **kwargs)

        if len(_teams) == 0:
            raise NotFoundError("No team criteria matches")
        if len(_teams) != 1:
            raise MultipleFoundError("Multiple teams fit criteria")

        return _teams[0]

    def teams(self, name=None, pk=None, is_hidden=False, **kwargs):
        """
        Teams of KE-chain.

        Provide a list of :class:`Team`s of KE-chain. You can filter on teamname or id or any other advanced filter.

        :param name: (optional) teamname to filter
        :type name: basestring or None
        :param pk: (optional) id of the team to filter
        :type pk: basestring or None
        :param is_hidden: (optional) boolean to show non-hidden or hidden teams or both (None) (default is non-hidden)
        :type is_hidden: bool or None
        :param kwargs: Additional filtering keyword=value arguments
        :type kwargs: dict or None
        :return: List of :class:`Teams`
        :raises NotFoundError: when a team could not be found
        """
        request_params = {
            'name': name,
            'id': pk,
            'is_hidden': is_hidden
        }
        if kwargs:
            request_params.update(**kwargs)

        response = self._request('GET', self._build_url('teams'), params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not find teams: '{}'".format(response.json()))

        data = response.json()
        return [Team(team, client=self) for team in data['results']]

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

    def _create_part1(self, action, data, **kwargs):
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

    def _create_part2(self, action, data, **kwargs):
        """Create a part for PIM 2 internal core function."""
        # suppress_kevents should be in the data (not the query_params)
        if 'suppress_kevents' in kwargs:
            data['suppress_kevents'] = kwargs.pop('suppress_kevents')

        # prepare url query parameters
        query_params = kwargs
        query_params.update(API_EXTRA_PARAMS['parts2'])

        response = self._request('POST', self._build_url('parts2_{}'.format(action)),
                                 params=query_params,
                                 json=data)

        if response.status_code != requests.codes.created:
            raise APIError("Could not create part, {}: {}".format(str(response), response.content))

        return Part2(response.json()['results'][0], client=self)

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
        if not isinstance(parent, Part) or not isinstance(model, Part):
            raise IllegalArgumentError("The parent and model should be a 'Part' object")
        if parent.category != Category.INSTANCE:
            raise IllegalArgumentError("The parent should be an category 'INSTANCE'")
        if model.category != Category.MODEL:
            raise IllegalArgumentError("The models should be of category 'MODEL'")

        if not name:
            name = model.name

        if self.match_app_version(label="gpim", version=">=2.0.0"):
            # PIM2
            data = dict(name=name, parent_id=parent.id, model_id=model.id)
            return self._create_part2(action="new_instance", data=data, **kwargs)
        else:
            # PIM1
            data = dict(name=name, parent=parent.id, model=model.id)
            return self._create_part1(action="new_instance", data=data, **kwargs)

    def create_model(self, parent, name, multiplicity=Multiplicity.ZERO_MANY, **kwargs):
        """Create a new child model under a given parent.

        In order to prevent the backend from updating the frontend you may add `suppress_kevents=True` as
        additional keyword=value argument to this method. This will improve performance of the backend
        against a trade-off that someone looking at the frontend won't notice any changes unless the page
        is refreshed.

        :param parent: parent part instance or a part uuid
        :type parent: :class:`models.Part`
        :param name: new part name
        :type name: basestring
        :param multiplicity: choose between ZERO_ONE, ONE, ZERO_MANY, ONE_MANY or M_N  :class:`enums.Multiplicity`
        :type multiplicity: basestring
        :param kwargs: (optional) additional keyword=value arguments
        :type kwargs: dict
        :return: :class:`models.Part` with category `MODEL` (from :class:`enums.Category`)
        :raises IllegalArgumentError: When the provided arguments are incorrect
        :raises APIError: if the `Part` could not be created
        """
        if parent.category != Category.MODEL:
            raise IllegalArgumentError("The parent should be of category 'MODEL'")

        if isinstance(parent, Part):
            pass
        elif is_uuid(parent):
            parent = self.model(id=parent)
        else:
            raise IllegalArgumentError("`parent` should be either a parent part or a uuid, got '{}'".format(parent))

        if self.match_app_version(label="gpim", version=">=2.0.0"):
            data = dict(name=name, parent_id=parent.id, multiplicity=multiplicity)
            return self._create_part2(action="create_child_model", data=data, **kwargs)
        else:
            data = dict(name=name, parent=parent.id, multiplicity=multiplicity)
            return self._create_part1(action="create_child_model", data=data, **kwargs)

    def create_model_with_properties(self, parent, name, multiplicity=Multiplicity.ZERO_MANY, properties_fvalues=None,
                                     **kwargs):
        """Create a model with its properties in a single API request.

        With KE-chain 3 backends you may now provide a whole set of properties to create using a `properties_fvalues`
        list of dicts.

        The `properties_fvalues` list is a list of dicts containing at least the `name` and `property_type`,
        but other keys may provided as well in the single update eg. `default_value` and `value_options`.

        Possible keys in a property dictionary are: `name` (req'd), `property_type` (req'd), `description`, `unit`,
        `value`, `value_options` (type: `dict`), `order` (type `int`).

        .. note::
           It is wise to provide an `order` to ensure that the properties are stored and retrieved in order.
           It cannot be guaranteed that the order of properties is the exact sequence of the list provided.

        .. versionadded:: 3.0
           This version makes a model including properties in a single API call

        :param parent: parent part instance or a part uuid
        :type parent: :class:`models.Part2`
        :param name: new part name
        :type name: basestring
        :param multiplicity: choose between ZERO_ONE, ONE, ZERO_MANY, ONE_MANY or M_N of :class:`enums.Multiplicity`
        :type multiplicity: basestring
        :param kwargs: (optional) additional keyword=value arguments
        :type kwargs: dict
        :return: :class:`models.Part` with category `MODEL` (of :class:`enums.Category`
        :raises IllegalArgumentError: When the provided arguments are incorrect
        :raises APIError: if the `Part` could not be created


        Example:
        --------
        >>> properties_fvalues = [
        ...     {"name": "char prop", "property_type": PropertyType.CHAR_VALUE, "order": 1},
        ...     {"name": "number prop", "property_type": PropertyType.FLOAT_VALUE, "value": 3.14, "order": 2},
        ...     {"name": "boolean_prop", "property_type": PropertyType.BOOLEAN_VALUE, "value": False,
        ...      "value_options": {"validators": [RequiredFieldValidator().as_json()]}, "order":3}
        ... ]
        >>> new_model = project.create_model_with_properties(name='A new model', parent='<uuid>',
        ...                                                  multiplicity=Multiplicity.ONE,
        ...                                                  properties_fvalues=properties_fvalues)

        """
        if not self.match_app_version(label="gpim", version=">=2.0.0"):
            # PIM1 world
            raise ClientError("This function only works for KE-chain 3 backends.")

        if isinstance(parent, Part):
            pass
        elif is_uuid(parent):
            parent = self.model(id=parent)
        else:
            raise IllegalArgumentError("`parent` should be either a parent part or a uuid, got '{}'".format(parent))

        if parent.category != Category.MODEL:
            raise IllegalArgumentError("The parent should be of category 'MODEL'")

        if isinstance(properties_fvalues, list):
            required_new_property_keys = ['name', 'property_type']
            for new_prop in properties_fvalues:
                if not all(k in new_prop.keys() for k in required_new_property_keys):
                    raise IllegalArgumentError("New property '{}' does not have a required field provided in the "
                                               "`properties_fvalues` list")
        else:
            raise IllegalArgumentError("`properties_fvalues` need to be provided as a list of dicts")

        data = dict(
            name=name,
            parent_id=parent.id,
            multiplicity=multiplicity,
            category=Category.MODEL,
            properties_fvalues=properties_fvalues
        )

        return self._create_part2(action="create_child_model", data=data, **kwargs)

    def _create_clone(self, parent, part, name=None, **kwargs):
        """Create a new `Part` clone under the `Parent`.

        An optional name of the cloned part may be provided. If not provided the name will be set
        to "CLONE - <part name>". (KE-chain 3 backends only)
        An optional multiplicity, may be added as paremeter for the cloning of models. If not
        provided the multiplicity of the part will be used.

        .. versionadded:: 2.3
        .. versionchanged:: 3.0
           Added the name parameter. Added option to add multiplicity as well.

        :param parent: parent part
        :type parent: :class:`models.Part`
        :param part: part to be cloned
        :type part: :class:`models.Part`
        :param name: (optional) Name of the to be cloned part
        :type name: basestring or None
        :param kwargs: (optional) additional keyword=value arguments
        :type kwargs: dict
        :return: cloned :class:`models.Part`
        :raises APIError: if the `Part` could not be cloned
        """
        if part.category == Category.MODEL:
            select_action = 'clone_model'
        else:
            select_action = 'clone_instance'
        if not isinstance(part, Part) and not isinstance(parent, Part):
            raise IllegalArgumentError("Either part and parent need to be of class `Part`. "
                                       "We got: part: '{}' and parent '{}'".format(type(part), type(parent)))

        if self.match_app_version(label="gpim", version=">=2.0.0"):
            data = dict(
                name=name or "CLONE - {}".format(part.name),
                parent_id=parent.id,
                suppress_kevents=kwargs.pop('suppress_kevents', None),
            )
            if part.category == Category.MODEL:
                data.update(dict(
                    multiplicity=kwargs.pop('multiplicity', part.multiplicity),
                    model_id=part.id)
                )
            else:
                data['instance_id'] = part.id
            query_params = kwargs
            query_params.update(API_EXTRA_PARAMS['parts2'])
            url = self._build_url('parts2_{}'.format(select_action))
        else:
            data = dict(
                part=part.id,
                parent=parent.id,
                suppress_kevents=kwargs.pop('suppress_kevents', None)
            )
            # prepare url query parameters
            query_params = kwargs
            query_params['select_action'] = select_action
            url = self._build_url('parts')

        response = self._request('POST', url, params=query_params, data=data)

        if response.status_code != requests.codes.created:
            raise APIError("Could not clone part, {}: {}".format(str(response), response.content))

        if self.match_app_version(label="gpim", version=">=2.0.0"):
            return Part2(response.json()['results'][0], client=self)
        else:
            return Part(response.json()['results'][0], client=self)

    def create_proxy_model(self, model, parent, name, multiplicity=Multiplicity.ZERO_MANY, **kwargs):
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

        if self.match_app_version(label="gpim", version=">=2.0.0"):
            data = dict(name=name, model_id=model.id, parent_id=parent.id, multiplicity=multiplicity)
            return self._create_part2(action='create_proxy_model', data=data, **kwargs)
        else:
            data = dict(name=name, model=model.id, parent=parent.id, multiplicity=multiplicity)
            return self._create_part1(action='create_proxy_model', data=data, **kwargs)

    def create_property(self, model, name, description=None, property_type=PropertyType.CHAR_VALUE, default_value=None,
                        unit=None, options=None, **kwargs):
        """Create a new property model under a given model.

        Use the :class:`enums.PropertyType` to select which property type to create to ensure that you
        provide the correct values to the KE-chain backend. The default is a `PropertyType.CHAR_VALUE` which is a
        single line text in KE-chain.

        .. versionchanged:: 3.0
           Changed for KE-chan 3 backend. Added optional additional properties.


        :param model: parent part model
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

        # if not property_type.endswith('_VALUE'):
        #     warnings.warn("Please use the `PropertyType` enumeration to ensure providing correct "
        #                   "values to the backend.", UserWarning)
        #     property_type = '{}_VALUE'.format(property_type.upper())

        if property_type not in PropertyType.values():
            raise IllegalArgumentError("Please provide a valid propertytype, please use one of `enums.PropertyType`. "
                                       "Got: '{}'".format(property_type))

        # because the references value only accepts a single 'model_id' in the default value, we need to convert this
        # to a single value from the list of values.
        if property_type in (PropertyType.REFERENCE_VALUE, PropertyType.REFERENCES_VALUE) and default_value:
            if isinstance(default_value, (list, tuple)):
                default_value = default_value[0]
            if isinstance(default_value, Part):
                default_value = default_value.id
            if not is_uuid(default_value):
                raise IllegalArgumentError("Please provide a valid default_value being a `Part` of category `MODEL` "
                                           "or a model uuid, got: '{}'".format(default_value))

        if self.match_app_version(label="gpim", version=">=2.0.0"):
            data = dict(
                name=name,
                part_id=model.id,
                description=description or '',
                property_type=property_type.upper(),
                value=default_value,
                unit=unit or '',
                value_options=options or {}
            )
            url = self._build_url('properties2_create_model')
            query_params = kwargs
            query_params.update(API_EXTRA_PARAMS['properties2'])
        else:
            data = dict(
                name=name,
                part=model.id,
                description=description or '',
                property_type=property_type.upper(),
                value=default_value,
                unit=unit or '',
                options=options or {}
            )
            url = self._build_url('properties')
            query_params = kwargs

        # # We add options after the fact only if they are available, otherwise the options will be set to null in the
        # # request and that can't be handled by KE-chain.
        # if options:
        #     data['options'] = options

        response = self._request('POST', url, params=query_params, json=data)

        if response.status_code != requests.codes.created:
            raise APIError("Could not create property, {}: {}".format(str(response), response.content))

        if self.match_app_version(label="gpim", version=">=2.0.0"):
            prop = Property2.create(response.json()['results'][0], client=self)
        else:
            prop = Property.create(response.json()['results'][0], client=self)

        model.properties.append(prop)

        return prop

    def create_service(self, name, scope, description=None, version=None,
                       service_type=ServiceType.PYTHON_SCRIPT,
                       environment_version=ServiceEnvironmentVersion.PYTHON_3_5, pkg_path=None):
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

        version = version or '1.0'  # 'script_version': ['This field may not be null.']
        description = description or ''  # 'description': ['This field may not be null.']

        data = dict(
            name=name,
            scope=scope,  # not scope_id!
            description=description,
            script_type=service_type,
            script_version=version,
            env_version=environment_version
        )

        response = self._request('POST', self._build_url('services'), json=data)

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not create service ({})".format((response, response.json())))

        service = Service(response.json().get('results')[0], client=self)

        if pkg_path:
            # upload the package / refresh of the service will be done in the upload function
            service.upload(pkg_path)

        return service

    def create_team(self, name, user, description=None, options=None, is_hidden=False):
        """
        Create a team.

        To create a team, a :class:`User` (id or object) need to be passed for it to become owner. As most pykechain
        enabled script are running inside the SIM environment in KE-chain, the user having the current connection
        to the API is often not the user that needs to be part of the team to be created. The user provided will
        become 'owner' of the team.

        .. versionadded: 2.4.0

        :param name: name of the team
        :type name: basestring
        :param user: user (userid, username or `User`) that will become owner of the team
        :type user: userid or username or :class:`models.User`
        :param description: (optional) description of the team
        :type name: basestring or None
        :param options: (optional) provide additional team advanced options (as dict)
        :type options: dict or None
        :param is_hidden: (optional) if the team needs to be hidden (defaults to false)
        :type is_hidden: bool or None
        :return: the created :class:`models.Team`
        :raises IllegalArgumentError: When the provided arguments are incorrect
        """
        if not isinstance(name, (string_types, text_type)):
            raise IllegalArgumentError('`name` should be string')
        if not isinstance(description, (string_types, text_type)):
            raise IllegalArgumentError('`description` should be string')
        if options and not isinstance(options, dict):
            raise IllegalArgumentError('`options` should be a dictionary')
        if is_hidden and not isinstance(is_hidden, bool):
            raise IllegalArgumentError('`is_hidden` should be a boolean')
        if isinstance(user, (string_types, text_type)):
            user = self.user(username=user)
        elif isinstance(user, int):
            user = self.user(pk=user)
        elif isinstance(user, User):
            pass
        else:
            raise IllegalArgumentError('the `user` is not of a type `User`, a `username` or a user id')

        data = dict(
            name=name,
            description=description,
            options=options,
            is_hidden=is_hidden
        )

        url = self._build_url('teams')
        response = self._request('POST', url, json=data)

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not create a team ({})".format((response, response.json())))

        the_team = Team(response.json().get('results')[0])

        the_team.add_members([user], role=TeamRoles.OWNER)
        team_members = the_team.members()
        the_team.remove_members([u for u in team_members if u != user])

        the_team.refresh()

    def clone_scope(self, source_scope, name=None, status=None, start_date=None, due_date=None,
                    description=None, team=None, async=False):
        """
        Clone a Scope.

        This will clone a scope if the client has the right to do so. Sufficient permissions to clone a scope are a
        superuser, a user in the `GG:Configurators` group and a user that is Scope manager of the scope to be
        clone and member of the `GG:Managers` group as well.

        If no additional arguments are provided, the values of the `source_scope` are used for the new scope.

        .. versionadded: 3.0

        :param source_scope: Scope object to be cloned itself
        :type source_scope: :class:`models.Scope`
        :param name: (optional) new name of the scope
        :type name: basestring or None
        :param status: (optional) statis of the new scope
        :type status: one of :class:`enums.ScopeStatus`
        # :param tags: (optional) list of new scope tags (NO EFFECT)
        # :type status: list of basestring or None
        :param start_date: (optional) start date of the to be cloned scope
        :type start_date: datetime or None
        :param due_date: (optional) due data of the to be cloned scope
        :type due_date: datetime or None
        :param description: (optional) description of the new scope
        :type description: basestring or None
        :param team: (optional) team_id or Team object to assign membership of scope to a team.
        :type team: basestring or :class:`models.Team` or None
        # :param scope_options: (optional) dictionary with scope options (NO EFFECT)
        # :type scope_options: dict or None
        :param async: (optional) option to use asynchronous cloning of the scope, default to False.
        :type async: bool or None
        :return: New scope that is cloned
        :rtype: :class:`models.Scope`
        :raises IllegalArgumentError: When the provided arguments are incorrect
        :raises APIError: When the server is unable to clone the scope (eg. permissions)
        """
        if not isinstance(source_scope, (Scope)):
            raise IllegalArgumentError('`source_scope` should be a `Scope` object')

        if self.match_app_version(label="gscope", version=">=2.0.0"):
            data_dict = dict(scope_id=source_scope.id,
                             async=async)
        else:
            data_dict = dict(id=source_scope.id,
                             async=async)

        if name is not None:
            if not isinstance(name, (string_types, text_type)):
                raise IllegalArgumentError("`name` should be a string")
            data_dict['name'] = str(name)

        if start_date is not None:
            if isinstance(start_date, datetime.datetime):
                if not due_date.tzinfo:
                    warnings.warn("The duedate '{}' is naive and not timezone aware, use pytz.timezone info. "
                                  "This date is interpreted as UTC time.".format(start_date.isoformat(sep=' ')))
                data_dict['start_date'] = start_date.isoformat(sep='T')
            else:
                raise IllegalArgumentError('Start date should be a datetime.datetime() object')

        if due_date is not None:
            if isinstance(due_date, datetime.datetime):
                if not due_date.tzinfo:
                    warnings.warn("The duedate '{}' is naive and not timezone aware, use pytz.timezone info. "
                                  "This date is interpreted as UTC time.".format(due_date.isoformat(sep=' ')))
                data_dict['due_date'] = due_date.isoformat(sep='T')
            else:
                raise IllegalArgumentError('Due date should be a datetime.datetime() object')

        if description is not None:
            if not isinstance(description, (text_type, string_types)):
                raise IllegalArgumentError("`description` should be a string")
            else:
                data_dict['text'] = description

        if status is not None:
            if not status in ScopeStatus.values():
                raise IllegalArgumentError("`status` should be one of '{}'".format(ScopeStatus.values()))
            else:
                data_dict['status'] = str(status)

        # TODO: fix in KEC3
        # if tags is not None:
        #     if not isinstance(tags, (list, tuple, set)) and not all(
        #             [isinstance(tag, (string_types, text_type)) for tag in tags]):
        #         raise IllegalArgumentError('`tags` should be a list (or tuple or set) of strings')
        #     else:
        #         data_dict['tags'] = list(set(tags))

        if team is not None:
            if isinstance(team, Team):
                team_id = team.id
            elif is_uuid(team):
                team_id = team
            elif isinstance(team, (text_type, string_types)):
                team_id = self.team(name=team).id
            else:
                raise IllegalArgumentError("`team` should be a name of an existing team or UUID of a team")

            if self.match_app_version(label="gscope", version=">=2.0.0"):
                data_dict['team_id'] = team_id
            else:
                data_dict['team'] = team_id

        # TODO: fix in KEC3
        # if scope_options is not None:
        #     if not isinstance(scope_options, dict):
        #         raise IllegalArgumentError("`scope_options` need to be a dictionary")
        #     else:
        #         if self.match_app_version(label="gpim", version=">=2.0.0"):
        #             data_dict['scope_options'] = scope_options
        #         else:
        #             data_dict['options'] = scope_options

        if self.match_app_version(label="gscope", version=">=2.0.0"):
            url = self._build_url('scopes2_clone')
            query_params = API_EXTRA_PARAMS['scopes2']
            response = self._request('POST', url,
                                     params=query_params,
                                     json=data_dict)
        else:
            url = self._build_url('scope')
            query_params = dict(select_action='clone')
            response = self._request('POST', url,
                                     query_params=query_params,
                                     json=data_dict)

        if response.status_code != requests.codes.created:  # pragma: no cover
            if response.status_code == requests.codes.forbidden:
                raise ForbiddenError("Could not clone scope, {}: {}".format(str(response), response.content))
            else:
                raise APIError("Could not clone scope, {}: {}".format(str(response), response.content))

        if self.match_app_version(label="gscope", version=">=2.0.0"):
            return Scope2(response.json()['results'][0], client=source_scope._client)
        else:
            return Scope(response.json()['results'][0], client=source_scope._client)
