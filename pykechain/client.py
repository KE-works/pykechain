import datetime
import warnings
from typing import Dict, Tuple, Optional, Any, List, Union, Text, Callable

import requests
from envparse import env
from requests.adapters import HTTPAdapter
from requests.compat import urljoin, urlparse  # type: ignore
from urllib3 import Retry

from pykechain.defaults import API_PATH, API_EXTRA_PARAMS, RETRY_ON_CONNECTION_ERRORS, RETRY_BACKOFF_FACTOR, \
    RETRY_TOTAL, RETRY_ON_READ_ERRORS, RETRY_ON_REDIRECT_ERRORS
from pykechain.enums import Category, KechainEnv, ScopeStatus, ActivityType, ServiceType, ServiceEnvironmentVersion, \
    PropertyType, TeamRoles, Multiplicity, ServiceScriptUser, WidgetTypes, \
    ActivityClassification, ActivityStatus
from pykechain.exceptions import ClientError, ForbiddenError, IllegalArgumentError, NotFoundError, MultipleFoundError, \
    APIError

from pykechain.models import Part2, Property2, Activity2, Scope2, PartSet, Base, AnyProperty, Service, \
        ServiceExecution
from pykechain.models.association import Association
from pykechain.models.team import Team
from pykechain.models.user import User
from pykechain.models.notification import Notification
from pykechain.models.widgets.widget import Widget
from pykechain.utils import is_uuid, find
from .__about__ import version as pykechain_version
from .models.input_checks import check_datetime, check_list_of_text, check_text, check_enum, check_type, \
    check_list_of_base, check_base, check_uuid, check_list_of_dicts, check_url
from .models.banner import Banner


class Client(object):
    """The KE-chain 2 python client to connect to a KE-chain (version 2) instance.

    :ivar last_request: last executed request. Which is of type `requests.Request`_
    :ivar last_response: last executed response. Which is of type `requests.Response`_
    :ivar last_url: last called api url

    .. _requests.Request: http://docs.python-requests.org/en/master/api/#requests.Request
    .. _requests.Response: http://docs.python-requests.org/en/master/api/#requests.Response
    """

    def __init__(self, url: Text = 'http://localhost:8000/', check_certificates: Optional[bool] = None) -> None:
        """Create a KE-chain client with given settings.

        :param url: the url of the KE-chain instance to connect to (defaults to http://localhost:8000)
        :type url: basestring
        :param check_certificates: if to check TLS/SSL Certificates. Defaults to True
        :type check_certificates: bool

        Examples
        --------
        >>> from pykechain import Client
        >>> client = Client()

        >>> from pykechain import Client
        >>> client = Client(url='https://default-tst.localhost:9443', check_certificates=False)

        """
        self.auth = None  # type: Optional[Tuple[str, str]]
        self.headers = {'X-Requested-With': 'XMLHttpRequest',
                        'PyKechain-Version': pykechain_version}  # type: Dict[str, str]
        self.session = requests.Session()  # type: requests.Session

        parsed_url = urlparse(url)
        if not (parsed_url.scheme and parsed_url.netloc):
            raise ClientError("Please provide a valid URL to a KE-chain instance")

        self.api_root = url
        self.headers = {'X-Requested-With': 'XMLHttpRequest',
                        'PyKechain-Version': pykechain_version}  # type: Dict[Text, Text]
        self.auth = None  # type: Optional[Tuple[Text, Text]]
        self.last_request = None  # type: Optional[requests.PreparedRequest]
        self.last_response = None  # type: Optional[requests.Response]
        self.last_url = None  # type: Optional[Text]
        self._app_versions = None  # type: Optional[List[Dict]]
        self._widget_schemas = None  # type: Optional[List[Dict]]

        if check_certificates is None:
            check_certificates = env.bool(KechainEnv.KECHAIN_CHECK_CERTIFICATES, default=True)

        if check_certificates is False:
            self.session.verify = False

        # Retry implementation
        adapter = HTTPAdapter(
            max_retries=Retry(total=RETRY_TOTAL,
                              connect=RETRY_ON_CONNECTION_ERRORS,
                              read=RETRY_ON_READ_ERRORS,
                              redirect=RETRY_ON_REDIRECT_ERRORS,
                              backoff_factor=RETRY_BACKOFF_FACTOR)
        )
        self.session.mount('https://', adapter=adapter)
        self.session.mount('http://', adapter=adapter)

    def __del__(self):
        """Destroy the client object."""
        self.session.close()
        del self.session
        del self.auth
        del self.headers

    def __repr__(self):  # pragma: no cover
        return "<pyke Client '{}'>".format(self.api_root)

    @classmethod
    def from_env(cls, env_filename: Optional[Text] = None, check_certificates: Optional[bool] = None) -> 'Client':
        """Create a client from environment variable settings.

        :param env_filename: filename of the environment file, defaults to '.env' in the local dir
                                        (or parent dir)
        :type env_filename: basestring
        :param check_certificates: if to check TLS/SSL Certificates. Defaults to True
        :type check_certificates: bool
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
        if check_certificates is None:
            check_certificates = env.bool(KechainEnv.KECHAIN_CHECK_CERTIFICATES, default=True)
        client = cls(url=env(KechainEnv.KECHAIN_URL), check_certificates=check_certificates)

        if env(KechainEnv.KECHAIN_TOKEN, None):
            client.login(token=env(KechainEnv.KECHAIN_TOKEN))
        elif env(KechainEnv.KECHAIN_USERNAME, None) and env(KechainEnv.KECHAIN_PASSWORD, None):
            client.login(username=env(KechainEnv.KECHAIN_USERNAME), password=env(KechainEnv.KECHAIN_PASSWORD))

        return client

    def login(self,
              username: Optional[Text] = None, password: Optional[Text] = None, token: Optional[Text] = None) -> None:
        """Login into KE-chain with either username/password or token.

        :param username: username for your user from KE-chain
        :type username: basestring
        :param password: password for your user from KE-chain
        :type password: basestring
        :param token: user authentication token retrieved from KE-chain
        :type token: basestring

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

    def _build_url(self, resource: Text, **kwargs) -> Text:
        """Build the correct API url.

        :param resource: name the resource from the API_PATH
        :type resource: basestring
        :param kwargs: (optional) id of the detail path to follow, eg. activity_id=...
        :return: url of the resource to the resource (id)
        """
        return urljoin(self.api_root, API_PATH[resource].format(**kwargs))

    def _retrieve_users(self) -> List[Dict]:
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

    def _request(self, method: Text, url: Text, **kwargs) -> requests.Response:
        """Perform the request on the API."""
        self.last_request = None
        if method in ('PUT', 'POST', 'DELETE'):
            kwargs['allow_redirects'] = False  # to prevent redirects on write action. Better check your URL first.
        self.last_response = self.session.request(method, url, auth=self.auth, headers=self.headers, **kwargs)
        self.last_request = self.last_response.request
        self.last_url = self.last_response.url

        if self.last_response.status_code == requests.codes.forbidden:
            raise ForbiddenError(self.last_response.json()['results'][0]['detail'])

        return self.last_response

    @property
    def app_versions(self) -> List[Dict]:
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

    @property
    def widget_schemas(self) -> Dict:
        """
        Widget meta schemas for all widgets in KE-chain 3.

        In KE-chain 3, the backend provides widget meta schema for each widgettype. A single call
        per pykechain client session is made (and cached forever in the client) to retrieve all
        widget schemas.

        ..versionadded:: 3.0

        :return: list of widget meta schemas
        :rtype: list of dict
        :raises APIError: When it could not retrieve the widget schemas
        :raises NotImplementedError: When the KE-chain version is lower than 3.
        """
        if self.match_app_version(label='pim', version='<3.0.0'):
            raise NotImplementedError('Widget schemas is not implemented in KE-chain versions lower that 3.0')
        if not self._widget_schemas:
            response = self._request('GET', self._build_url('widgets_schemas'))
            if response.status_code != requests.codes.ok:  # pragma: no cover
                raise APIError("Could not retrieve widgets schemas ({})".format((response, response.json())))
            self._widget_schemas = response.json().get('results')

        return self._widget_schemas

    def widget_schema(self, widget_type: Text) -> Dict:
        """Widget schema for widget type.

        ..versionadded:: 3.0

        :param widget_type: Type of the widget to return the widgetschema for.
        :type widget_type: basestring
        :returns: dictionary with jsonschema to validate the widget meta
        :rtype: dict
        :raises APIError: When it could not retrieve the jsonschema from KE-chain
        :raises NotFoundError: When it could not find the correct schema
        """
        check_enum(widget_type, WidgetTypes, 'widget_type')

        found = find(self.widget_schemas, lambda ws: ws.get('widget_type') == widget_type)
        if not found:
            raise NotFoundError("Could not find a widget_schema for widget_type: `{}`".format(widget_type))
        return found

    def match_app_version(
            self,
            app: Optional[Text] = None,
            label: Optional[Text] = None,
            version: Optional[Text] = None,
            default: Optional[bool] = False,
    ) -> bool:
        """Match app version against a semantic version string.

        Checks if a KE-chain app matches a version comparison. Uses the `semver` matcher to check.

        `match("2.0.0", ">=1.0.0")` => `True`
        `match("1.0.0", ">1.0.0")` => `False`

        Examples
        --------
        >>> client = Client()
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

    def reload(self, obj: Base, url: Optional[Text] = None, extra_params: Optional[Dict] = None):
        """Reload an object from server. The original object is immutable and it will return a new object.

        The object will be refetched from KE-chain. If the object has a 'url' field the url will be taken from
        that field (KE-chain version 2 and newer). If the object does not have an 'url' field it will be constructed
        based on the class name and the id of the object itself. If `extra_params` are provided, these will be
        respected. If additional API params are needed to be included (eg. for KE-chain 3/PIM2) these will be
        added/updated automatically before the request is performed.

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
            # TODO Throw an error instead of building the URL?
            #  This .__name__ method does not work for subclasses (e.g. MultiReferenceProperty).

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

    @staticmethod
    def _retrieve_singular(method: Callable, *args, **kwargs):
        """
        Use the method for multiple objects to retrieve a single object, raising the appropriate errors.

        :param method: function used to retrieve multiple objects.
        :type method: callable
        :return the single result
        :raises NotFoundError: When no result is found.
        :raises MultipleFoundError: When more than a single result is found.
        """
        results = method(*args, **kwargs)

        criteria = '\nargs: {}\nkwargs: {}'.format(args, kwargs)

        if len(results) == 0:
            raise NotFoundError("No {} fit criteria:{}".format(method.__name__, criteria))
        if len(results) != 1:
            raise MultipleFoundError("Multiple {} fit criteria:{}".format(method.__name__, criteria))

        return results[0]

    def scopes(
            self,
            name: Optional[Text] = None,
            pk: Optional[Text] = None,
            status: Optional[Union[ScopeStatus, Text]] = ScopeStatus.ACTIVE,
            **kwargs
    ) -> List[Scope2]:
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
            'name': check_text(text=name, key='name'),
            'id': check_uuid(pk),
            'status': check_enum(status, ScopeStatus, 'status'),
        }

        request_params.update(API_EXTRA_PARAMS['scope2'])
        url = self._build_url('scopes2')

        if kwargs:
            request_params.update(**kwargs)

        response = self._request('GET', url=url, params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve scopes: '{}'".format(response.content))

        data = response.json()

        return [Scope2(s, client=self) for s in data['results']]

    def scope(self, *args, **kwargs) -> Scope2:
        """Return a single scope based on the provided name.

        If additional `keyword=value` arguments are provided, these are added to the request parameters. Please
        refer to the documentation of the KE-chain API for additional query parameters.

        :return: a single :class:`models.Scope`
        :raises NotFoundError: When no `Scope` is found
        :raises MultipleFoundError: When more than a single `Scope` is found
        """
        return self._retrieve_singular(self.scopes, *args, **kwargs)

    def activities(
            self,
            name: Optional[Text] = None,
            pk: Optional[Text] = None,
            scope: Optional[Text] = None,
            **kwargs
    ) -> List[Activity2]:
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
            'id': check_uuid(pk),
            'name': check_text(text=name, key='name'),
            'scope': scope
        }

        request_params.update(API_EXTRA_PARAMS['activity'])

        if kwargs:
            request_params.update(**kwargs)

        response = self._request('GET', self._build_url('activities'), params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve activities. Server responded with {}".format(str(response)))

        data = response.json()
        return [Activity2(a, client=self) for a in data['results']]

    def activity(self, *args, **kwargs) -> Activity2:
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
        return self._retrieve_singular(self.activities, *args, **kwargs)

    def parts(
            self,
            name: Optional[Text] = None,
            pk: Optional[Text] = None,
            model: Optional[Part2] = None,
            category: Optional[Union[Category, Text]] = Category.INSTANCE,
            scope_id: Optional[Text] = None,
            parent: Optional[Text] = None,
            activity: Optional[Text] = None,
            widget: Optional[Text] = None,
            limit: Optional[int] = None,
            batch: Optional[int] = 100,
            **kwargs
    ) -> PartSet:
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
        :param scope_id: filter on scope_id
        :type scope_id: basestring or None
        :param parent: filter on the parent_id, returns all children of the parent_id
        :type parent: basestring or None
        :param activity: filter on activity_id
        :type activity: basestring or None
        :param widget: filter on widget_id
        :type activity: basestring or None
        :param limit: limit the return to # items (default unlimited, so return all results)
        :type limit: int or None
        :param batch: limit the batch size to # items (defaults to 100 items per batch)
        :type batch: int or None
        :param kwargs: additional `keyword=value` arguments for the api
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
            id=check_uuid(pk),
            name=check_text(text=name, key='name'),
            category=check_enum(category, Category, 'category'),
            activity_id=activity,
            widget_id=widget,
            limit=batch,
            scope_id=scope_id,
            parent_id=parent,
            model_id=model.id if model else None,
        )
        url = self._build_url('parts2')
        request_params.update(API_EXTRA_PARAMS['parts2'])

        if kwargs:
            request_params.update(**kwargs)

        response = self._request('GET', url, params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve parts. Request: {}\nResponse: {}".format(
                request_params, response.content))

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

        return PartSet((Part2(p, client=self) for p in part_results))

    def part(self, *args, **kwargs) -> Part2:
        """Retrieve single KE-chain part.

        Uses the same interface as the :func:`parts` method but returns only a single pykechain :class:`models.Part`
        instance.

        If additional `keyword=value` arguments are provided, these are added to the request parameters. Please
        refer to the documentation of the KE-chain API for additional query parameters.

        :return: a single :class:`models.Part`
        :raises NotFoundError: When no `Part` is found
        :raises MultipleFoundError: When more than a single `Part` is found
        """
        return self._retrieve_singular(self.parts, *args, **kwargs)

    def model(self, *args, **kwargs) -> Part2:
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
        return self._retrieve_singular(self.parts, *args, **kwargs)

    def properties(
            self,
            name: Optional[Text] = None,
            pk: Optional[Text] = None,
            category: Optional[Union[Category, Text]] = Category.INSTANCE,
            **kwargs
    ) -> List['AnyProperty']:
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
        :return: list of :class:`models.Property`
        :raises NotFoundError: When no `Property` is found
        """
        request_params = {
            'name': check_text(text=name, key='name'),
            'id': check_uuid(pk),
            'category': check_enum(category, Category, 'category')
        }
        if kwargs:  # pragma: no cover
            request_params.update(**kwargs)

        request_params.update(API_EXTRA_PARAMS['properties2'])
        response = self._request('GET', self._build_url('properties2'), params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve properties: '{}'".format(response.content))

        return [Property2.create(p, client=self) for p in response.json()['results']]

    def property(self, *args, **kwargs) -> 'AnyProperty':  # noqa: F
        """Retrieve single KE-chain Property.

        Uses the same interface as the :func:`properties` method but returns only a single pykechain :class:
        `models.Property` instance.

        If additional `keyword=value` arguments are provided, these are added to the request parameters. Please
        refer to the documentation of the KE-chain API for additional query parameters.

        :return: a single :class:`models.Property`
        :raises NotFoundError: When no `Property` is found
        :raises MultipleFoundError: When more than a single `Property` is found
        """
        return self._retrieve_singular(self.properties, *args, **kwargs)

    def services(
            self,
            name: Optional[Text] = None,
            pk: Optional[Text] = None,
            scope: Optional[Text] = None,
            **kwargs
    ) -> List[Service]:
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
        :return: list of :class:`models.Service` objects
        :raises NotFoundError: When no `Service` objects are found
        """
        request_params = {
            'name': check_text(text=name, key='name'),
            'id': check_uuid(pk),
            'scope': scope
        }
        request_params.update(API_EXTRA_PARAMS['service'])

        if kwargs:
            request_params.update(**kwargs)

        response = self._request('GET', self._build_url('services'), params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve services")

        return [Service(service, client=self) for service in response.json()['results']]

    def service(self, *args, **kwargs):
        """
        Retrieve single KE-chain Service.

        Uses the same interface as the :func:`services` method but returns only a single pykechain
        :class:`models.Service` instance.

        :param kwargs: (optional) additional search keyword arguments
        :return: a single :class:`models.Service` object
        :raises NotFoundError: When no `Service` object is found
        :raises MultipleFoundError: When more than a single `Service` object is found
        """
        return self._retrieve_singular(self.services, *args, **kwargs)

    def service_executions(
            self,
            name: Optional[Text] = None,
            pk: Optional[Text] = None,
            scope: Optional[Text] = None,
            service: Optional[Text] = None,
            **kwargs
    ) -> List[ServiceExecution]:
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
        :return: a single :class:`models.ServiceExecution` object
        :raises NotFoundError: When no `ServiceExecution` object is found
        """
        request_params = {
            'name': check_text(text=name, key='name'),
            'id': check_uuid(pk),
            'service': service,
            'scope': scope
        }
        if kwargs:
            request_params.update(**kwargs)

        response = self._request('GET', self._build_url('service_executions'), params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve service executions")

        return [ServiceExecution(service_exeuction, client=self) for service_exeuction in response.json()['results']]

    def service_execution(self, *args, **kwargs):
        """
        Retrieve single KE-chain ServiceExecution.

        Uses the same interface as the :func:`service_executions` method but returns only a single
        pykechain :class:`models.ServiceExecution` instance.

        If additional `keyword=value` arguments are provided, these are added to the request parameters. Please
        refer to the documentation of the KE-chain API for additional query parameters.

        :param kwargs: (optional) additional search keyword arguments
        :return: a single :class:`models.ServiceExecution` object
        :raises NotFoundError: When no `ServiceExecution` object is found
        :raises MultipleFoundError: When more than a single `ServiceExecution` object is found
        """
        return self._retrieve_singular(self.service_executions, *args, **kwargs)

    def users(self, username: Optional[Text] = None, pk: Optional[Text] = None, **kwargs) -> List[User]:
        """
        Users of KE-chain.

        Provide a list of :class:`User`'s of KE-chain. You can filter on username or id or any other advanced filter.

        :param username: (optional) username to filter
        :type username: basestring or None
        :param pk: (optional) id of the user to filter
        :type pk: basestring or None
        :param kwargs: Additional filtering keyword=value arguments
        :return: List of :class:`Users`
        :raises NotFoundError: when a user could not be found
        """
        request_params = {
            'username': check_text(text=username, key='username'),
            'id': check_type(pk, (str, int), 'pk'),
        }
        if kwargs:
            request_params.update(**kwargs)

        response = self._request('GET', self._build_url('users'), params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not find users: '{}'".format(response.json()))

        return [User(user, client=self) for user in response.json()['results']]

    def user(self, *args, **kwargs):
        """
        User of KE-chain.

        Provides single user of :class:`User` of KE-chain. You can filter on username or id or an advanced filter.

        :param kwargs: Additional filtering keyword=value arguments
        :return: List of :class:`User`
        :raises NotFoundError: when a user could not be found
        :raises MultipleFoundError: when more than a single user can be found
        """
        return self._retrieve_singular(self.users, *args, **kwargs)

    def teams(
            self,
            name: Optional[Text] = None,
            pk: Optional[Text] = None,
            is_hidden: Optional[bool] = False,
            **kwargs
    ) -> List[Team]:
        """
        Teams of KE-chain.

        Provide a list of :class:`Team`'s of KE-chain. You can filter on teamname or id or any other advanced filter.

        :param name: (optional) teamname to filter
        :type name: basestring or None
        :param pk: (optional) id of the team to filter
        :type pk: basestring or None
        :param is_hidden: (optional) boolean to show non-hidden or hidden teams or both (None) (default is non-hidden)
        :type is_hidden: bool or None
        :param kwargs: Additional filtering keyword=value arguments
        :return: List of :class:`Teams`
        :raises NotFoundError: when a team could not be found
        """
        request_params = {
            'name': check_text(text=name, key='name'),
            'id': check_uuid(pk),
            'is_hidden': is_hidden
        }
        if kwargs:
            request_params.update(**kwargs)

        response = self._request('GET', self._build_url('teams'), params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not find teams: '{}'".format(response.json()))

        return [Team(team, client=self) for team in response.json()['results']]

    def team(self, *args, **kwargs):
        """
        Team of KE-chain.

        Provides a team of :class:`Team` of KE-chain. You can filter on team name or provide id.

        :param kwargs: Additional filtering keyword=value arguments
        :return: List of :class:`Team`
        :raises NotFoundError: when a user could not be found
        :raises MultipleFoundError: when more than a single user can be found
        """
        return self._retrieve_singular(self.teams, *args, **kwargs)

    def widgets(
            self,
            pk: Optional[Text] = None,
            activity: Optional[Union[Activity2, Text]] = None,
            **kwargs
    ) -> List[Widget]:
        """
        Widgets of an activity.

        Only works for KE-chain version 3.

        :param pk: (optional) the uuid of the widget.
        :type pk: basestring or None
        :param activity: (optional) the :class:`Activity` or UUID of the activity to filter the widgets for.
        :type activity: basestring or None
        :param kwargs: additional keyword arguments
        :return: A :class:`WidgetManager` list, containing the widgets
        :rtype: WidgetManager
        :raises NotFoundError: when the widgets could not be found
        :raises APIError: when the API does not support the widgets, or when the API gives an error.
        """
        """Widgets of an activity."""
        request_params = dict(API_EXTRA_PARAMS['widgets'])
        request_params['id'] = check_uuid(pk)

        if isinstance(activity, Activity2):
            request_params.update(dict(activity_id=activity.id))
        elif is_uuid(activity):
            request_params.update(dict(activity_id=activity))

        if kwargs:
            request_params.update(**kwargs)

        response = self._request('GET', self._build_url('widgets'), params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not find widgets: '{}'".format(response.json()))

        return [Widget.create(json=json, client=self) for json in response.json()['results']]

    #
    # Creators
    #

    def create_activity(
            self,
            parent: Union[Activity2, Text],
            name: Text,
            activity_type: ActivityType = ActivityType.TASK,
            status: ActivityStatus = ActivityStatus.OPEN,
            description: Optional[Text] = None,
            start_date: Optional[datetime.datetime] = None,
            due_date: Optional[datetime.datetime] = None,
            classification: ActivityClassification = None,
            tags: Optional[List[Text]] = None,
    ) -> Activity2:
        """
        Create a new activity.

        :param parent: parent under which to create the activity
        :type parent: basestring or :class:`models.Activity2`
        :param name: new activity name
        :type name: basestring
        :param activity_type: type of activity: TASK (default) or PROCESS
        :type activity_type: basestring
        :param status: status of the activity: OPEN (default) or COMPLETED
        :type status: ActivityStatus
        :param description: description of the activity
        :type description: basestring
        :param start_date: starting date of the activity
        :type start_date: datetime.datetime
        :param due_date: due date of the activity
        :type due_date: datetime.datetime
        :param classification: classification of activity: defaults to `parent`'s if provided, WORKFLOW otherwise.
        :type classification: ActivityClassification
        :param tags: list of activity tags
        :type tags: list
        :return: the created :class:`models.Activity2`
        :raises APIError: When the object could not be created
        :raises IllegalArgumentError: When an incorrect arguments are provided
        """
        if isinstance(parent, Activity2):
            parent_classification = parent.classification
            parent_id = parent.id
        elif is_uuid(parent):
            parent_classification = None
            parent_id = parent
        else:
            raise IllegalArgumentError('`parent` must be an Activity or UUID, "{}" is neither'.format(parent))

        if classification is None:
            if parent_classification is None:
                classification = ActivityClassification.WORKFLOW
            else:
                classification = parent_classification
        else:
            classification = check_enum(classification, ActivityClassification, 'classification')

        data = {
            "name": check_text(text=name, key='name'),
            "parent_id": parent_id,
            "status": check_enum(status, ActivityStatus, 'status'),
            "activity_type": check_enum(activity_type, ActivityType, 'activity_type'),
            "classification": classification,
            "description": check_text(text=description, key='description'),
            "start_date": check_datetime(dt=start_date, key='start_date'),
            "due_date": check_datetime(dt=due_date, key='due_date'),
            "tags": check_list_of_text(tags, key='tags'),
        }

        response = self._request('POST', self._build_url('activities'), data=data,
                                 params=API_EXTRA_PARAMS['activities'])

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not create activity {}: {}".format(str(response), response.content))

        new_activity = Activity2(data['results'][0], client=self)
        if isinstance(parent, Activity2) and parent._cached_children is not None:
            parent._cached_children.append(new_activity)
        return new_activity

    def _create_part(self, action: Text, data: Dict, **kwargs) -> Optional[Part2]:
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

    def create_part(self, parent: Part2, model: Part2, name: Optional[Text] = None, **kwargs) -> Part2:
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
        if not isinstance(parent, Part2) or not isinstance(model, Part2):
            raise IllegalArgumentError("The `parent` and `model` should be 'Part' objects")
        if parent.category != Category.INSTANCE:
            raise IllegalArgumentError("The `parent` should be of category 'INSTANCE'")
        if model.category != Category.MODEL:
            raise IllegalArgumentError("The `model` should be of category 'MODEL'")

        name = check_text(text=name, key='name') or model.name

        data = dict(name=name, parent_id=parent.id, model_id=model.id)
        return self._create_part(action="new_instance", data=data, **kwargs)

    def create_model(self,
                     parent: Union[Part2, Text],
                     name: Text,
                     multiplicity: Optional[Multiplicity] = Multiplicity.ZERO_MANY,
                     **kwargs) -> Part2:
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
        :return: :class:`models.Part` with category `MODEL` (from :class:`enums.Category`)
        :raises IllegalArgumentError: When the provided arguments are incorrect
        :raises APIError: if the `Part` could not be created
        """
        if isinstance(parent, Part2):
            pass
        elif is_uuid(parent):
            parent = self.model(id=parent)
        else:
            raise IllegalArgumentError("`parent` should be either a parent part or a uuid, got '{}'".format(parent))

        if parent.category != Category.MODEL:
            raise IllegalArgumentError("The parent should be of category 'MODEL'")

        data = dict(
            name=check_text(name, 'name'),
            parent_id=parent.id,
            multiplicity=check_enum(multiplicity, Multiplicity, 'multiplicity'),
        )
        return self._create_part(action="create_child_model", data=data, **kwargs)

    def create_model_with_properties(
            self,
            parent: Union[Part2, Text],
            name: Text,
            multiplicity: Optional[Multiplicity] = Multiplicity.ZERO_MANY,
            properties_fvalues: Optional[List[Dict]] = None,
            **kwargs) -> Part2:
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
        :param properties_fvalues: list of dicts per property, each must have fields `name` and `property_type`.
        :type properties_fvalues: list
        :param kwargs: (optional) additional keyword=value arguments
        :return: :class:`models.Part` with category `MODEL` (of :class:`enums.Category`)
        :raises IllegalArgumentError: When the provided arguments are incorrect
        :raises APIError: if the `Part` could not be created


        Example
        -------
        >>> from pykechain.models.validators import RequiredFieldValidator
        >>> properties_fvalues = [
        ...     {"name": "char prop", "property_type": PropertyType.CHAR_VALUE, "order": 1},
        ...     {"name": "number prop", "property_type": PropertyType.FLOAT_VALUE, "value": 3.14, "order": 2},
        ...     {"name": "boolean_prop", "property_type": PropertyType.BOOLEAN_VALUE, "value": False,
        ...      "value_options": {"validators": [RequiredFieldValidator().as_json()]}, "order":3}
        ... ]
        >>> client = Client()
        >>> new_model = client.create_model_with_properties(name='A new model', parent='<uuid>',
        ...                                                 multiplicity=Multiplicity.ONE,
        ...                                                 properties_fvalues=properties_fvalues)

        """
        if isinstance(parent, Part2):
            pass
        elif is_uuid(parent):
            parent = self.model(id=parent)
        else:
            raise IllegalArgumentError("`parent` should be either a parent part or a uuid, got '{}'".format(parent))

        if parent.category != Category.MODEL:
            raise IllegalArgumentError("`parent` should be of category 'MODEL'")

        data = dict(
            name=check_text(text=name, key='name'),
            parent_id=parent.id,
            multiplicity=check_enum(multiplicity, Multiplicity, 'multiplicity'),
            category=Category.MODEL,
            properties_fvalues=check_list_of_dicts(properties_fvalues, 'properties_fvalues', ['name', 'property_type']),
        )

        return self._create_part(action="create_child_model", data=data, **kwargs)

    def _create_clone(self,
                      parent: Part2,
                      part: Part2,
                      name: Optional[Text] = None,
                      multiplicity: Optional[Multiplicity] = None,
                      **kwargs
                      ) -> Part2:
        """Create a new `Part` clone under the `Parent`.

        An optional name of the cloned part may be provided. If not provided the name will be set
        to "CLONE - <part name>". (KE-chain 3 backends only)

        .. versionadded:: 2.3
        .. versionchanged:: 3.0
           Added the name parameter. Added option to add multiplicity as well.

        :param parent: parent part
        :type parent: :class:`models.Part`
        :param part: part to be cloned
        :type part: :class:`models.Part`
        :param name: (optional) Name of the to be cloned part
        :type name: basestring or None
        :param multiplicity: In case of Models, to specify a new multiplicity. Defaults to the `part` multiplicity.
        :type multiplicity: Multiplicity
        :param kwargs: (optional) additional keyword=value arguments
        :return: cloned :class:`models.Part`
        :raises APIError: if the `Part` could not be cloned
        """
        check_type(part, Part2, 'part')
        check_type(parent, Part2, 'parent')

        data = dict(
            name=check_text(name, 'name') or "CLONE - {}".format(part.name),
            parent_id=parent.id,
            suppress_kevents=kwargs.pop('suppress_kevents', None),
        )

        if part.category == Category.MODEL:
            data.update({
                'multiplicity': check_enum(multiplicity, Multiplicity, 'multiplicity') or part.multiplicity,
                'model_id': part.id,
            })
        else:
            data['instance_id'] = part.id

        if part.category == Category.MODEL:
            select_action = 'clone_model'
        else:
            select_action = 'clone_instance'

        query_params = kwargs
        query_params.update(API_EXTRA_PARAMS['parts2'])
        url = self._build_url('parts2_{}'.format(select_action))

        response = self._request('POST', url, params=query_params, data=data)

        if response.status_code != requests.codes.created:
            raise APIError("Could not clone part, {}: {}".format(str(response), response.content))

        return Part2(response.json()['results'][0], client=self)

    def create_proxy_model(
            self,
            model: Part2,
            parent: Part2,
            name: Text,
            multiplicity: Optional[Multiplicity] = Multiplicity.ZERO_MANY,
            **kwargs
    ) -> Part2:
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
        :return: the new proxy :class:`models.Part` with category `MODEL`
        :raises IllegalArgumentError: When the provided arguments are incorrect
        :raises APIError: if the `Part` could not be created
        """
        check_type(model, Part2, 'model')
        check_type(parent, Part2, 'parent')

        if model.category != Category.MODEL:
            raise IllegalArgumentError("The model should be of category MODEL")
        if parent.category != Category.MODEL:
            raise IllegalArgumentError("The parent should be of category MODEL")

        data = dict(
            name=check_text(text=name, key='name'),
            model_id=model.id,
            arent_id=parent.id,
            multiplicity=check_enum(multiplicity, Multiplicity, 'multiplicity'),
        )
        return self._create_part(action='create_proxy_model', data=data, **kwargs)

    def create_property(
            self,
            model: Part2,
            name: Text,
            description: Optional[Text] = None,
            property_type: Optional[Union[PropertyType, Text]] = PropertyType.CHAR_VALUE,
            default_value: Optional[Any] = None,
            unit: Optional[Text] = None,
            options: Optional[Dict] = None,
            **kwargs
    ) -> AnyProperty:
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
        check_enum(property_type, PropertyType, 'property_type')
        check_type(model, Part2, 'model')
        if model.category != Category.MODEL:
            raise IllegalArgumentError("`model` should be of category MODEL")

        options = check_type(options, dict, 'options') or dict()

        if property_type in (PropertyType.REFERENCE_VALUE, PropertyType.REFERENCES_VALUE) and default_value:
            # References only accept a single 'model_id' in the default value, we need to convert
            # this to a single value from the list of values.
            if isinstance(default_value, (list, tuple)):
                default_value = default_value[0]

            # Retrieve the referenced Scope from the default value
            if isinstance(default_value, Part2):
                scope_options = dict(
                    scope_id=default_value._json_data["scope_id"]
                )
                default_value = [default_value.id]
            elif is_uuid(default_value):
                scope_options = dict(
                    scope_id=self.model(id=default_value)._json_data["scope_id"]
                )
                default_value = [default_value]
            else:
                raise IllegalArgumentError("Please provide a valid `default_value` being a `Part` of category `MODEL` "
                                           "or a model uuid, got: '{}'".format(default_value))
            options.update(scope_options)

        data = dict(
            name=check_text(name, 'name'),
            part_id=model.id,
            description=check_text(description, 'description') or '',
            property_type=property_type.upper(),
            value=default_value,
            unit=unit or '',
            value_options=options,
        )
        url = self._build_url('properties2_create_model')
        query_params = kwargs
        query_params.update(API_EXTRA_PARAMS['properties2'])

        response = self._request('POST', url, params=query_params, json=data)

        if response.status_code != requests.codes.created:
            raise APIError("Could not create property, {}: {}".format(str(response), response.content))

        prop = Property2.create(response.json()['results'][0], client=self)

        model.properties.append(prop)

        return prop

    def create_service(
            self,
            name: Text,
            scope: Scope2,
            description: Optional[Text] = None,
            version: Optional[Text] = None,
            service_type: Optional[ServiceType] = ServiceType.PYTHON_SCRIPT,
            environment_version: Optional[ServiceEnvironmentVersion] = ServiceEnvironmentVersion.PYTHON_3_6,
            run_as: Optional[ServiceScriptUser] = ServiceScriptUser.KENODE_USER,
            pkg_path: Optional[Text] = None
    ) -> Service:
        """
        Create a Service.

        A service can be created only providing the name (and scope). Other information can be added later.
        If you provide a path to the `kecpkg` (or python script) to upload (`pkg_path`) on creation,
        this `kecpkg` will be uploaded in one go. If the later fails, the service is still there, and the package is
        not uploaded.

        Permission to upload a script is restricted to a superuser, a user in the `GG:Configurators` group and a Scope
        Manager of the scope to which you are uploading the script.

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
         :class:`pykechain.enums.ServiceEnvironmentVersion`), defaults to `PYTHON_3_6`
        :type environment_version: basestring or None
        :param run_as: (optional) user to run the service as. Defaults to kenode user (bound to scope)
        :type run_as: basestring or None
        :param pkg_path: (optional) full path name to the `kecpkg` (or python script) to upload
        :type pkg_path: basestring or None
        :return: the created :class:`models.Service`
        :raises IllegalArgumentError: When the provided arguments are incorrect
        :raises APIError: In case of failure of the creation or failure to upload the pkg_path
        :raises OSError: In case of failure to locate the `pkg_path`
        """
        data = dict(
            name=check_text(name, 'name'),
            scope=check_base(scope, Scope2, 'scope'),  # not scope_id!
            description=check_text(text=description, key='description') or '',
            script_type=check_enum(service_type, ServiceType, 'service_type'),
            script_version=check_text(text=version, key='version') or '1.0',
            env_version=check_enum(environment_version, ServiceEnvironmentVersion, 'environment_version'),
            run_as=check_enum(run_as, ServiceScriptUser, 'run_as')
        )

        response = self._request('POST', self._build_url('services'), json=data)

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not create service ({})".format((response, response.json())))

        service = Service(response.json().get('results')[0], client=self)

        if pkg_path:
            # upload the package / refresh of the service will be done in the upload function
            service.upload(pkg_path)

        return service

    def create_scope(
            self,
            name: Text,
            status: Optional[ScopeStatus] = ScopeStatus.ACTIVE,
            description: Optional[Text] = None,
            tags: Optional[List[Text]] = None,
            start_date: Optional[datetime.datetime] = None,
            due_date: Optional[datetime.datetime] = None,
            team: Optional[Union[Team, Text]] = None,
            **kwargs
    ) -> Scope2:
        """
        Create a Scope.

        This will create a scope if the client has the right to do so. Sufficient permissions to create a scope are a
        superuser, a user in the `GG:Configurators` group or `GG:Managers` group.

        ..versionadded: 2.6

        :param name: Name of the scope
        :type name: basestring
        :param status: choose one of the :class:`enums.ScopeStatus`, defaults to `ScopeStatus.ACTIVE`
        :type status: basestring or None
        :param description: (optional) Description of the scope
        :type description: basestring or None
        :param tags: (optional) List of tags to be added to the new scope
        :type tags: list or None
        :param start_date: (optional) start date of the scope. Will default to 'now' if not provided.
        :type start_date: datetime.datetime or None
        :param due_date: (optional) due date of the scope
        :type due_date: datetime.datetime or None
        :param team: (optional) team_id or Team object to assign membership of scope to a team.
        :type team: basestring or :class:`models.Team` or None
        :param kwargs: optional additional search arguments
        :return: the created :class:`models.Scope`
        :raises APIError: In case of failure of the creation of new Scope
        """
        start_date = start_date if start_date else datetime.datetime.now()

        data_dict = {
            'name': check_text(name, 'name'),
            'status': check_enum(status, ScopeStatus, 'status'),
            'text': check_text(description, 'description'),
            'tags': check_list_of_text(tags, 'tags'),
            'start_date': check_datetime(dt=start_date, key='start_date'),
            'due_date': check_datetime(dt=due_date, key='due_date'),
            'team_id': check_base(team, Team, 'team', method=self.team),
        }

        # injecting additional kwargs for those cases that you need to add extra options.
        data_dict.update(kwargs)

        url = self._build_url('scopes2')
        query_params = API_EXTRA_PARAMS['scopes2']
        response = self._request('POST', url, params=query_params, data=data_dict)

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not create scope, {}:\n\n{}'".format(str(response), response.json()))

        return Scope2(response.json()['results'][0], client=self)

    def delete_scope(self, scope: Scope2, asynchronous: Optional[bool] = True) -> bool:
        """
        Delete a scope.

        This will delete a scope if the client has the right to do so. Sufficient permissions to delete a scope are a
        superuser, a user in the `GG:Configurators` group or a user that is the Scope manager of the scope to be
        deleted.

        :param scope: Scope object to be deleted
        :type scope: :class: `models.Scope`
        :param asynchronous: (optional) if the scope deletion should be performed asynchronous (default True)
        :type asynchronous: bool
        :return: True when the delete is a success.
        :raises APIError: in case of failure in the deletion of the scope
        """
        check_type(scope, Scope2, 'scope')

        query_options = {
            "async_mode": check_type(asynchronous, bool, 'asynchronous'),
        }

        response = self._request('DELETE',
                                 url=self._build_url('scope2', scope_id=str(scope.id)),
                                 params=query_options)

        if response.status_code != requests.codes.no_content:  # pragma: no cover
            raise APIError("Could not delete scope, {}: {}".format(str(response), response.content))

        return True

    def clone_scope(
            self,
            source_scope: Scope2,
            name: Optional[Text] = None,
            status: Optional[ScopeStatus] = None,
            start_date: Optional[datetime.datetime] = None,
            due_date: Optional[datetime.datetime] = None,
            description: Optional[Text] = None,
            tags: Optional[List[Text]] = None,
            team: Optional[Union[Team, Text]] = None,
            scope_options: Optional[Dict] = None,
            asynchronous: Optional[bool] = False,
    ) -> Optional[Scope2]:
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
        :param tags: (optional) list of new scope tags
        :type tags: list or None
        :param start_date: (optional) start date of the to be cloned scope
        :type start_date: datetime or None
        :param due_date: (optional) due data of the to be cloned scope
        :type due_date: datetime or None
        :param description: (optional) description of the new scope
        :type description: basestring or None
        :param team: (optional) team_id or Team object to assign membership of scope to a team.
        :type team: basestring or :class:`models.Team` or None
        :param scope_options: (optional) dictionary with scope options (NO EFFECT)
        :type scope_options: dict or None
        :param asynchronous: (optional) option to use asynchronous cloning of the scope, default to False.
        :type asynchronous: bool or None
        :return: New scope that is cloned
        :rtype: :class:`models.Scope`
        :raises IllegalArgumentError: When the provided arguments are incorrect
        :raises APIError: When the server is unable to clone the scope (eg. permissions)
        """
        check_type(source_scope, Scope2, 'scope')
        check_type(scope_options, dict, 'scope_options')

        start_date = start_date or source_scope.start_date
        due_date = due_date or source_scope.due_date

        data_dict = {
            'scope_id': source_scope.id,
            'name': check_text(name, 'name') or 'CLONE - {}'.format(source_scope.name),
            'start_date': check_datetime(dt=start_date, key='start_date'),
            'due_date': check_datetime(dt=due_date, key='due_date'),
            'text': check_text(description, 'description') or source_scope.description,
            'status': check_enum(status, ScopeStatus, 'status'),
            'tags': check_list_of_text(tags, 'tags') or source_scope.tags,
            'scope_options': scope_options or dict(),
            'async_mode': asynchronous,
        }

        team = check_base(team, Team, 'team', method=self.team)
        if team:
            data_dict['team_id'] = team

        url = self._build_url('scopes2_clone')
        query_params = API_EXTRA_PARAMS['scopes2']
        response = self._request('POST', url,
                                 params=query_params,
                                 json=data_dict)

        if response.status_code != requests.codes.created:  # pragma: no cover
            if response.status_code == requests.codes.forbidden:
                raise ForbiddenError("Could not clone scope, {}: {}".format(str(response), response.content))
            else:
                raise APIError("Could not clone scope, {}: {}".format(str(response), response.content))

        if asynchronous:
            return None

        cloned_scope = Scope2(response.json()['results'][0], client=source_scope._client)

        # TODO work-around, some attributes are not (yet) in the KE-chain response.json()
        cloned_scope._tags = tags
        cloned_scope.start_date = start_date
        cloned_scope.due_date = due_date
        return cloned_scope

    def create_team(
            self,
            name: Text,
            user: Union[Text, int, User],
            description: Optional[Text] = None,
            options: Optional[Dict] = None,
            is_hidden: Optional[bool] = False
    ) -> Team:
        """
        Create a team.

        To create a team, a :class:`User` (id or object) need to be passed for it to become owner. As most pykechain
        enabled script are running inside the SIM environment in KE-chain, the user having the current connection
        to the API is often not the user that needs to be part of the team to be created. The user provided will
        become 'owner' of the team.

        .. versionadded: 3.0

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
        :raises APIError: When an API Error occurs
        """
        if isinstance(user, str):
            user = self.user(username=user)
        elif isinstance(user, int):
            user = self.user(pk=user)
        elif isinstance(user, User):
            pass
        else:
            raise IllegalArgumentError('the `user` is not of a type `User`, a `username` or a user id')

        data = dict(
            name=check_text(name, 'name'),
            description=check_text(description, 'description'),
            options=check_type(options, dict, 'options') or dict(),
            is_hidden=check_type(is_hidden, bool, 'is_hidden'),
        )

        url = self._build_url('teams')
        response = self._request('POST', url, json=data)

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not create a team ({})".format((response, response.json())))

        new_team = Team(json=response.json().get('results')[0], client=self)

        new_team.add_members([user], role=TeamRoles.OWNER)
        team_members = new_team.members()

        members_to_remove = [self.user(username=u.get('username')) for u in team_members if u.get(
            'username') != user.username]

        if members_to_remove:
            new_team.remove_members(members_to_remove)
            new_team.refresh()

        return new_team

    @staticmethod
    def _validate_widget(
            activity: Union[Activity2, Text],
            widget_type: Union[WidgetTypes, Text],
            title: Optional[Text],
            meta: Dict,
            order: Optional[int],
            parent: Optional[Union[Widget, Text]],
            **kwargs
    ) -> Dict:
        """Validate the format and content of the configuration of a widget."""
        data = dict(
            activity_id=check_base(activity, Activity2, 'activity'),
            widget_type=check_enum(widget_type, WidgetTypes, 'widget_type'),
            meta=meta,
            parent_id=check_base(parent, Widget, 'parent')
        )

        title = check_text(title, 'title')
        if title is not None and not title.strip():
            raise IllegalArgumentError("`title` can not be empty")
        if title:
            data['title'] = title

        check_type(order, int, 'order')
        if order is not None:
            data['order'] = order

        if kwargs:
            data.update(**kwargs)

        return data

    @staticmethod
    def _validate_related_models(readable_models: List, writable_models: List, **kwargs) -> Tuple[List, List]:
        """
        Verify the format and content of the readable and writable models.

        :param readable_models: list of Properties or UUIDs
        :param writable_models: list of Properties or UUIDs
        :param kwargs: option to insert "inputs" and "outputs", instead of new inputs.
        :return: Tuple with both input lists, now with only UUIDs
        :rtype Tuple[List, List]
        """
        if kwargs.get('inputs'):
            readable_models = kwargs.pop('inputs')
        if kwargs.get('outputs'):
            writable_models = kwargs.pop('outputs')

        readable_model_ids = check_list_of_base(readable_models, Property2, 'readable_models')
        writable_model_ids = check_list_of_base(writable_models, Property2, 'writable_models')

        return readable_model_ids, writable_model_ids

    def create_widget(
            self,
            activity: Union[Activity2, Text],
            widget_type: Union[WidgetTypes, Text],
            meta: Dict,
            title: Optional[Text] = None,
            order: Optional[int] = None,
            parent: Optional[Union[Widget, Text]] = None,
            readable_models: Optional[List] = None,
            writable_models: Optional[List] = None,
            **kwargs
    ) -> Widget:
        """
        Create a widget inside an activity.

        If you want to associate models (and instances) in a single go, you may provide a list of `Property`
        (models) to the `readable_model_ids` or `writable_model_ids`.

        Alternatively you can use the alias, `inputs` and `outputs` which connect to respectively
        `readable_model_ids` and `writable_models_ids`.

        :param activity: activity objects to create the widget in.
        :type activity: :class:`Activity` or UUID
        :param widget_type: type of the widget, one of :class:`WidgetTypes`
        :type: string
        :param meta: meta dictionary of the widget.
        :type meta: dict
        :param title: (optional) title of the widget
        :type title: str or None
        :param order: (optional) order in the activity of the widget.
        :type order: int or None
        :param parent: (optional) parent of the widget for Multicolumn and Multirow widget.
        :type parent: :class:`Widget` or UUID
        :param readable_models: (optional) list of property model ids to be configured as readable (alias = inputs)
        :type readable_models: list of properties or list of property id's
        :param writable_models: (optional) list of property model ids to be configured as writable (alias = ouputs)
        :type writable_models: list of properties or list of property id's
        :param kwargs: (optional) additional keyword=value arguments to create widget
        :return: the created subclass of :class:`Widget`
        :rtype: :class:`Widget`
        :raises IllegalArgumentError: when an illegal argument is send.
        :raises APIError: when an API Error occurs.
        """
        data = self._validate_widget(
            activity=activity,
            widget_type=widget_type,
            title=title,
            meta=meta,
            order=order,
            parent=parent,
            **kwargs
        )

        readable_model_ids, writable_model_ids = self._validate_related_models(
            readable_models=readable_models,
            writable_models=writable_models,
            **kwargs,
        )

        # perform the call
        url = self._build_url('widgets')
        response = self._request('POST', url, params=API_EXTRA_PARAMS['widgets'], json=data)

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not create a widget ({})\n\n{}".format(response, response.json().get('traceback')))

        # create the widget and do postprocessing
        widget = Widget.create(json=response.json().get('results')[0], client=self)

        # update the associations if needed
        if readable_model_ids is not None or writable_model_ids is not None:
            widget.update_associations(readable_models=readable_model_ids, writable_models=writable_model_ids)

        return widget

    def create_widgets(self, widgets: List[Dict], **kwargs) -> List[Widget]:
        """
        Bulk-create of widgets.

        :param widgets: list of dictionaries defining the configuration of the widget.
        :type widgets: List[Dict]
        :return: list of `Widget` objects
        :rtype List[Widget]
        """
        bulk_data = list()
        bulk_associations = list()
        for widget in widgets:
            data = self._validate_widget(
                activity=widget.get('activity'),
                widget_type=widget.get('widget_type'),
                title=widget.get('title'),
                meta=widget.get('meta'),
                order=widget.get('order'),
                parent=widget.get('parent'),
                **widget.pop('kwargs', dict()),
            )
            bulk_data.append(data)

            bulk_associations.append(self._validate_related_models(
                readable_models=widget.get('readable_models'),
                writable_models=widget.get('writable_models'),
                **widget.pop('kwargs', dict()),
            ))

        url = self._build_url('widgets_bulk_create')
        response = self._request('POST', url, params=API_EXTRA_PARAMS['widgets'], json=bulk_data)

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not create a widgets ({})\n\n{}".format(response, response.json().get('traceback')))

        # create the widget and do postprocessing
        widgets = []
        for widget_response in response.json().get('results'):
            widget = Widget.create(json=widget_response, client=self)
            widgets.append(widget)

        self.update_widgets_associations(widgets=widgets, associations=bulk_associations, **kwargs)

        return widgets

    def update_widgets(self, widgets: List[Dict]) -> List[Widget]:
        """
        Bulk-update of widgets.

        :param widgets: list of widget configurations.
        :type widgets: List[Dict]
        :return: list of Widget objects
        :rtype List[Widget]
        """
        check_list_of_dicts(widgets, 'widgets')

        response = self._request(
            "PUT",
            self._build_url('widgets_bulk_update'),
            params=API_EXTRA_PARAMS['widgets'],
            json=widgets,
        )

        if response.status_code != requests.codes.ok:
            raise APIError("Could not update the widgets: {}: {}".format(str(response), response.content))

        widgets_response = response.json().get('results')
        return [Widget.create(json=widget_json, client=self) for widget_json in widgets_response]

    def delete_widget(self, widget: Union[Widget, Text]) -> None:
        """
        Delete a single Widget.

        :param widget: Widget or its UUID to be deleted
        :type widget: Widget or basestring
        :return: None
        :raises APIError: whenever the widget could not be deleted
        :raises IllegalArgumentError: whenever the input `widget` is invalid
        """
        widget = check_base(widget, Widget, 'widget')
        url = self._build_url('widget', widget_id=widget)
        response = self._request('DELETE', url)

        if response.status_code != requests.codes.no_content:  # pragma: no cover
            raise APIError("Could not delete Widget ({})".format(response))

    def delete_widgets(self, widgets: List[Union[Widget, Text]]) -> None:
        """
        Delete multiple Widgets.

        :param widgets: List, Tuple or Set of Widgets or their UUIDs to be deleted
        :type widgets: List[Union[Widget, Text]]
        :return: None
        :raises APIError: whenever the widgets could not be deleted
        :raises IllegalArgumentError: whenever the input `widgets` is invalid
        """
        widget_ids = check_list_of_base(widgets, Widget, 'widgets')

        url = self._build_url('widgets_bulk_delete')
        response = self._request('DELETE', url, json=widget_ids)

        if response.status_code != requests.codes.no_content:
            raise APIError("Could not delete the widgets: {}: {}".format(str(response), response.content))

    @staticmethod
    def _validate_associations(
            widgets: List[Union[Widget, Text]],
            associations: List[Tuple[List, List]],
    ) -> List[Text]:
        """Perform the validation of the internal widgets and associations."""
        widget_ids = check_list_of_base(widgets, Widget, 'widgets')

        if not isinstance(associations, List) and all(isinstance(a, tuple) and len(a) == 2 for a in associations):
            raise IllegalArgumentError(
                '`associations` must be a list of tuples, defining the readable and writable models per widget.')

        if not len(widgets) == len(associations):
            raise IllegalArgumentError('The `widgets` and `associations` lists must be of equal length, '
                                       'not {} and {}.'.format(len(widgets), len(associations)))

        return widget_ids

    def associations(
            self,
            widget: Optional[Widget] = None,
            activity: Optional[Activity2] = None,
            part: Optional[Part2] = None,
            property: Optional[AnyProperty] = None,
            scope: Optional[Scope2] = None,
            limit: Optional[int] = None,
    ) -> List[Association]:
        """
        Retrieve a list of associations.

        :param widget: widget for which to retrieve associations
        :type widget: Widget
        :param activity: activity for which to retrieve associations
        :type activity: Activity2
        :param part: part for which to retrieve associations
        :type part: Part2
        :param property: property for which to retrieve associations
        :type property: AnyProperty
        :param scope: scope for which to retrieve associations
        :type scope: Scope2
        :param limit: maximum number of associations to retrieve
        :type limit: int
        :return: list of association objects
        :rtype List[Association]
        """
        part = check_type(part, Part2, 'part')
        if part is not None:
            if part.category == Category.MODEL:
                part_instance = ''
                part_model = part.id
            else:
                part_instance = part.id
                part_model = ''
        else:
            part_instance = ''
            part_model = ''

        prop = check_type(property, Property2, 'property')
        if prop is not None:
            if prop.category == Category.MODEL:
                property_model = prop.id
                property_instance = ''
            else:
                property_model = ''
                property_instance = prop.id
        else:
            property_instance = ''
            property_model = ''

        limit = check_type(limit, int, 'limit') or ''
        if limit and limit < 1:
            raise IllegalArgumentError('`limit` is not a positive integer!')

        request_params = {
            'limit': limit,
            'widget': check_base(widget, Widget, 'widget') or '',
            'activity': check_base(activity, Activity2, 'activity') or '',
            'scope': check_base(scope, Scope2, 'scope') or '',
            'instance_part': part_instance,
            'instance_property': property_instance,
            'model_part': part_model,
            'model_property': property_model,
        }

        url = self._build_url('associations')
        response = self._request('GET', url, params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not retrieve associations ({})".format((response, response.json())))

        associations = [Association(json=r, client=self) for r in response.json()['results']]

        return associations

    def update_widget_associations(
            self,
            widget: Union[Widget, Text],
            readable_models: Optional[List] = None,
            writable_models: Optional[List] = None,
            **kwargs
    ) -> None:
        """
        Update associations on this widget.

        This is a patch to the list list of associations. Existing associations are not replaced.

        :param widget: widget to update associations for
        :type widget: :class:`Widget` or UUID
        :param readable_models: list of property models (of :class:`Property` or property_ids (uuids) that has
                                   read rights
        :type readable_models: List[Property2] or List[UUID] or None
        :param writable_models: list of property models (of :class:`Property` or property_ids (uuids) that has
                                   write rights
        :type writable_models: List[Property2] or List[UUID] or None
        :return: None
        :raises APIError: when the associations could not be changed
        :raise IllegalArgumentError: when the list is not of the right type
        """
        self.update_widgets_associations(
            widgets=[widget],
            associations=[(
                readable_models if readable_models else [],
                writable_models if writable_models else [],
            )],
            **kwargs
        )

    def update_widgets_associations(
            self,
            widgets: List[Union[Widget, Text]],
            associations: List[Tuple[List, List]],
            **kwargs
    ) -> None:
        """
        Update associations on multiple widgets in bulk.

        This is patch to the list of associations. Existing associations are not replaced.

        :param widgets: list of widgets to update associations for.
        :type widgets: :class: list
        :param associations: list of tuples, each tuple containing 2 lists of properties
                             (of :class:`Property` or property_ids (uuids)
        :type associations: List[Tuple]
        :return: None
        :raises APIError: when the associations could not be changed
        :raise IllegalArgumentError: when the list is not of the right type
        """
        widget_ids = self._validate_associations(widgets, associations)

        bulk_data = list()
        for widget_id, association in zip(widget_ids, associations):
            readable_models, writable_models = association

            readable_model_ids, writable_model_ids = self._validate_related_models(
                readable_models=readable_models,
                writable_models=writable_models,
            )

            data = dict(
                id=widget_id,
                readable_model_properties_ids=readable_model_ids,
                writable_model_properties_ids=writable_model_ids,
            )

            if kwargs:
                data.update(**kwargs)

            bulk_data.append(data)

        # perform the call
        url = self._build_url('widgets_update_associations')
        response = self._request('PUT', url, params=API_EXTRA_PARAMS['widgets'], json=bulk_data)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update associations of the widgets ({})".format((response, response.json())))

        return None

    def set_widget_associations(
            self,
            widget: Union[Widget, Text],
            readable_models: Optional[List] = None,
            writable_models: Optional[List] = None,
            **kwargs
    ) -> None:
        """
        Update associations on this widget.

        This is an absolute list of associations. If no property model id's are provided, then the associations are
        emptied out and replaced with no associations.

        :param widget: widget to set associations for.
        :type widget: :class:`Widget` or UUID
        :param readable_models: list of property models (of :class:`Property` or property_ids (uuids) that has
                                   read rights
        :type readable_models: List[Property2] or List[UUID] or None
        :param writable_models: list of property models (of :class:`Property` or property_ids (uuids) that has
                                   write rights
        :type writable_models: List[Property2] or List[UUID] or None
        :return: None
        :raises APIError: when the associations could not be changed
        :raise IllegalArgumentError: when the list is not of the right type
        """
        self.set_widgets_associations(
            widgets=[widget],
            associations=[(readable_models, writable_models)],
            **kwargs
        )

    def set_widgets_associations(
            self,
            widgets: List[Union[Widget, Text]],
            associations: List[Tuple[List, List]],
            **kwargs
    ) -> None:
        """
        Set associations on multiple widgets in bulk.

        This is an absolute list of associations. If no property model id's are provided, then the associations are
        emptied out and replaced with no associations.

        :param widgets: list of widgets to set associations for.
        :type widgets: :class: list
        :param associations: list of tuples, each tuple containing 2 lists of properties
                             (of :class:`Property` or property_ids (uuids)
        :type associations: List[Tuple]
        :return: None
        :raises APIError: when the associations could not be changed
        :raise IllegalArgumentError: when the list is not of the right type
        """
        widget_ids = self._validate_associations(widgets, associations)

        bulk_data = list()
        for widget_id, association in zip(widget_ids, associations):
            readable_models, writable_models = association

            readable_model_ids, writable_model_ids = self._validate_related_models(
                readable_models=readable_models,
                writable_models=writable_models,
            )

            data = dict(
                id=widget_id,
                readable_model_properties_ids=readable_model_ids,
                writable_model_properties_ids=writable_model_ids,
            )

            if kwargs:  # pragma: no cover
                data.update(**kwargs)

            bulk_data.append(data)

        # perform the call
        url = self._build_url('widgets_set_associations')
        response = self._request('PUT', url, params=API_EXTRA_PARAMS['widgets'], json=bulk_data)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not set associations of the widgets ({})".format((response, response.json())))

        return None

    def clear_widget_associations(
            self,
            widget: Widget,
    ) -> None:
        """
        Remove all associations of a widget.

        :param widget: widget to clear associations from.
        :type widget: Widget
        :return: None
        :raises APIError: when the associations could not be cleared.
        :raise IllegalArgumentError: if the widget is not of type Widget
        """
        check_type(widget, Widget, 'widget')

        # perform the call
        url = self._build_url('widget_clear_associations', widget_id=widget.id)
        response = self._request(method='PUT', url=url)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not clear associations of widget ({})".format((response, response.json())))

        return None

    def remove_widget_associations(
            self,
            widget: Widget,
            models: Optional[List[Union['AnyProperty', Text]]] = (),
            **kwargs
    ) -> None:
        """
        Remove specific associations from a widget.

        :param widget: widget to remove associations from.
        :type widget: Widget
        :param models: list of Property models or their UUIDs
        :type models: list
        :return: None
        :raises APIError: when the associations could not be removed
        :raise IllegalArgumentError: if the widget is not of type Widget
        """
        check_type(widget, Widget, 'widget')

        model_ids = check_list_of_base(models, Property2, 'models')

        if not model_ids:
            return

        data = dict(
            id=widget.id,
            model_properties_ids=model_ids,
        )

        # perform the call
        url = self._build_url('widget_remove_associations', widget_id=widget.id)
        response = self._request(method='PUT', url=url, params=API_EXTRA_PARAMS['widget'], json=data)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not remove associations of widget ({})".format((response, response.json())))

        return

    def move_activity(self, activity, parent, classification=None):
        """
        Move the `Activity` and, if applicable, its sub-tree to another parent.

        If you want to move an Activity from one classification to another, you need to provide the target
        classification. The classificaiton of the parent should match the one provided in the function. This is
        to ensure that you really want this to happen.

        .. versionadded:: 2.7

        .. versionchanged:: 3.1
           Add ability to move activity from one classification to another.

        :param activity: The `Activity` object to be moved.
        :type activity: :class: `Activity`
        :param parent: The parent `Subprocess` under which this `Activity` will be moved.
        :type parent: :class:`Activity` or UUID
        :param classification: The target classification if it is desirable to change ActivityClassification
        :type classification: Text
        :raises IllegalArgumentError: if the 'parent' activity_type is not :class:`enums.ActivityType.SUBPROCESS`
        :raises IllegalArgumentError: if the 'parent' type is not :class:`Activity2` or UUID
        :raises APIError: if an Error occurs.
        """
        activity = check_type(activity, Activity2, 'activity')

        if isinstance(parent, Activity2):
            parent_object = parent
        elif isinstance(parent, str) and is_uuid(parent):
            parent_object = self.activity(id=parent)
        else:
            raise IllegalArgumentError("Please provide either an activity object or a UUID")

        if parent_object.activity_type != ActivityType.PROCESS:
            raise IllegalArgumentError("One can only move an `Activity` under a subprocess.")

        update_dict = {
            'parent_id': parent_object.id,
            'classification': check_enum(
                classification, ActivityClassification, 'classification') or parent_object.classification,
        }

        url = self._build_url('activity_move', activity_id=str(activity.id))
        response = self._request('PUT', url, data=update_dict)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not move activity, {}: {}".format(str(response), response.content))

    def update_properties(self, properties: List[Dict]) -> List['AnyProperty']:
        """
        Update multiple properties simultaneously.

        :param properties: list of dictionaries to set the properties
        :type properties: List[Dict]
        :raises: IllegalArgumentError
        :return: list of Properties
        :rtype List[AnyProperty]
        """
        check_list_of_dicts(properties, 'properties')

        response = self._request(
            'POST',
            self._build_url('properties2_bulk_update'),
            params=API_EXTRA_PARAMS['property2'],
            json=properties,
        )

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Properties ({})".format(response))

        properties = [Property2.create(client=self, json=js) for js in response.json()['results']]

        return properties

    def notifications(self, pk: Optional[Text] = None, **kwargs) -> List[Notification]:
        """Retrieve one or more notifications stored on the instance.

        If additional `keyword=value` arguments are provided, these are added to the request parameters. Please
        refer to the documentation of the KE-chain API for additional query parameters.

        :param pk: if provided, filter the search by notification_id
        :type pk: basestring or None
        :param kwargs: (optional) additional search keyword arguments
        :return: list of :class:`models.Notification` objects
        :raises APIError: When the retrieval call failed due to various reasons
        """
        request_params = {
            'id': check_uuid(pk)
        }

        if kwargs:
            request_params.update(**kwargs)

        response = self._request('GET', self._build_url('notifications'), params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not retrieve Notifications. Request: {}\nResponse: {}".format(
                request_params, response.content))

        data = response.json()

        return [Notification(notification, client=self) for notification in data['results']]

    def notification(self, pk: Optional[Text] = None, *args, **kwargs) -> Notification:
        """Retrieve a single KE-chain notification.

        Uses the same interface as the :func:`notifications` method but returns only a single pykechain
        :class:`models.Notification` object.

        If additional `keyword=value` arguments are provided, these are added to the request parameters. Please
        refer to the documentation of the KE-chain API for additional query parameters.

        :param pk: if provided, filter the search by notification_id
        :type pk: basestring or None
        :param kwargs: (optional) additional search keyword arguments
        :return: a single :class:`models.Notification`
        :raises NotFoundError: When no `Notification` is found based on the search arguments
        :raises MultipleFoundError: When more than a single `Notification` is found based on the search arguments
        """
        return self._retrieve_singular(self.notifications, pk=pk, *args, **kwargs)

    def create_notification(self, **kwargs) -> Notification:
        """
        Create a single `Notification`.

        :param kwargs: (optional) keyword=value arguments
        :return: the newly created `Notification`
        :raises: APIError: when the `Notification` could not be created
        """
        query_params = kwargs
        query_params.update(API_EXTRA_PARAMS['notifications'])

        url = self._build_url('notifications')

        response = self._request('POST', url, data=query_params)

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not create notification, {}:\n\n{}'".format(str(response), response.json()))

        notification = Notification(response.json().get('results')[0], client=self)
        return notification

    def delete_notification(self, notification: Union[Notification, Text]) -> None:
        """
        Delete a single Notification.

        :param notification: Notification or its UUID to be deleted
        :type notification: Notification or basestring
        :return: None
        :raises APIError: whenever the notification could not be deleted
        :raises IllegalArgumentError: whenever the input `notification` is invalid
        """
        notification = check_base(notification, Notification, 'notification')

        url = self._build_url('notification', notification_id=notification)
        response = self._request('DELETE', url)

        if response.status_code != requests.codes.no_content:  # pragma: no cover
            raise APIError("Could not delete Notification ({})".format(response))

    def banners(
            self,
            pk: Optional[Text] = None,
            text: Optional[Text] = None,
            is_active: Optional[bool] = None,
            **kwargs
    ) -> List[Banner]:
        """
        Retrieve Banners.

        :param pk: ID of the banner
        :param text: Text displayed in the banner
        :param is_active: Whether the banner is currently active
        :return: list of Banner objects
        :rtype list
        """
        request_params = {
            'text': check_text(text, 'text'),
            'id': check_uuid(pk),
            'is_active': check_type(is_active, bool, 'is_active'),
        }
        request_params.update(API_EXTRA_PARAMS['banners'])

        if kwargs:  # pragma: no cover
            request_params.update(**kwargs)

        response = self._request('GET', self._build_url('banners'), params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve banners")

        data = response.json()
        return [Banner(banner, client=self) for banner in data['results']]

    def banner(self, *args, **kwargs) -> Banner:
        """
        Retrieve a single Banner, see `banners()` for available arguments.

        :return: single banner
        :rtype Banner
        """
        return self._retrieve_singular(self.banners, *args, **kwargs)

    def create_banner(
            self,
            text: Text,
            icon: Text,
            active_from: datetime.datetime,
            active_until: Optional[datetime.datetime] = None,
            is_active: Optional[bool] = False,
            url: Optional[Text] = None,
            **kwargs
    ) -> Banner:
        """
        Create a new banner.

        :param text: Text to display in the banner. May use HTML.
        :type text: str
        :param icon: Font-awesome icon to stylize the banner
        :type icon: str
        :param active_from: Datetime from when the banner will become active.
        :type active_from: datetime.datetime
        :param active_until: Datetime from when the banner will no longer be active.
        :type active_until: datetime.datetime
        :param is_active: Boolean whether to set the banner as active, defaults to False.
        :type is_active: bool
        :param url: target for the "more info" button within the banner.
        :param url: str
        :param kwargs: additional arguments for the request
        :return: the new banner
        :rtype Banner
        """
        data = {
            'text': check_text(text, 'text'),
            'icon': check_text(icon, 'icon'),
            'active_from': check_datetime(active_from, 'active_from'),
            'active_until': check_datetime(active_until, 'active_until'),
            'is_active': check_type(is_active, bool, 'is_active'),
            'url': check_url(url),
        }

        # prepare url query parameters
        query_params = kwargs
        query_params.update(API_EXTRA_PARAMS['banners'])

        response = self._request('POST', self._build_url('banners'),
                                 params=query_params,
                                 json=data)

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not create banner, {}: {}".format(str(response), response.content))

        return Banner(response.json()['results'][0], client=self)

    def active_banner(self) -> Optional[Banner]:
        """
        Retrieve the currently active banner.

        :return: Banner object. If no banner is active, returns None.
        :rtype Banner
        """
        response = self._request('GET', self._build_url('banner_active'))

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve banners")

        data = response.json()['results'][0]
        return Banner(json=data, client=self) if data else None
