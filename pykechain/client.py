import datetime
import warnings
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from urllib.parse import urljoin, urlparse

import requests
from envparse import env
from requests.adapters import HTTPAdapter  # type: ignore

from pykechain.defaults import (
    API_EXTRA_PARAMS,
    API_PATH,
    PARTS_BATCH_LIMIT,
    RETRY_BACKOFF_FACTOR,
    RETRY_ON_CONNECTION_ERRORS,
    RETRY_ON_READ_ERRORS,
    RETRY_ON_REDIRECT_ERRORS,
    RETRY_TOTAL,
)
from pykechain.enums import (
    ActivityClassification,
    ActivityStatus,
    ActivityType,
    Category,
    ContextGroup,
    ContextType,
    FormCategory,
    KechainEnv,
    LanguageCodes,
    Multiplicity,
    NotificationChannels,
    NotificationEvent,
    NotificationStatus,
    PropertyType,
    ScopeStatus,
    ServiceEnvironmentVersion,
    ServiceScriptUser,
    ServiceType,
    StoredFileCategory,
    StoredFileClassification,
    TeamRoles,
    WidgetTypes,
    WorkflowCategory,
)
from pykechain.exceptions import (
    APIError,
    ClientError,
    ForbiddenError,
    IllegalArgumentError,
    MultipleFoundError,
    NotFoundError,
)
from pykechain.models import (
    Activity,
    AnyProperty,
    Base,
    Part,
    PartSet,
    Property,
    Scope,
    Service,
    ServiceExecution,
)
from pykechain.models.association import Association
from pykechain.models.notification import Notification
from pykechain.models.team import Team
from pykechain.models.user import User
from pykechain.models.widgets.widget import Widget
from pykechain.utils import (
    clean_empty_values,
    find,
    get_in_chunks,
    is_uuid,
    is_valid_email,
    slugify_ref,
)
from .__about__ import version as pykechain_version
from .client_utils import PykeRetry
from .models.banner import Banner
from .models.context import Context
from .models.expiring_download import ExpiringDownload
from .models.form import Form
from .models.input_checks import (
    check_base,
    check_date,
    check_datetime,
    check_enum,
    check_list_of_base,
    check_list_of_dicts,
    check_list_of_text,
    check_text,
    check_time,
    check_type,
    check_url,
    check_user,
    check_uuid,
)
from .models.stored_file import StoredFile
from .models.workflow import Workflow
from .typing import ObjectID


class Client:
    """The KE-chain python client to connect to a KE-chain instance.

    :ivar last_request: last executed request. Which is of type `requests.Request`_
    :ivar last_response: last executed response. Which is of type `requests.Response`_
    :ivar last_url: last called api url

    .. _requests.Request: http://docs.python-requests.org/en/master/api/#requests.Request
    .. _requests.Response: http://docs.python-requests.org/en/master/api/#requests.Response
    """

    def __init__(
        self,
        url: str = "http://localhost:8000/",
        check_certificates: Optional[bool] = None,
    ) -> None:
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
        self.auth: Optional[Tuple[str, str]] = None
        self.headers: Dict[str, str] = {
            "X-Requested-With": "XMLHttpRequest",
            "PyKechain-Version": pykechain_version,
        }
        self.session: requests.Session = requests.Session()

        parsed_url = urlparse(url)
        if not (parsed_url.scheme and parsed_url.netloc):
            raise ClientError("Please provide a valid URL to a KE-chain instance")

        self.api_root = url
        self.headers: Dict[str, str] = {
            "X-Requested-With": "XMLHttpRequest",
            "PyKechain-Version": pykechain_version,
        }
        self.auth: Optional[Tuple[str, str]] = None
        self.last_request: Optional[requests.PreparedRequest] = None
        self.last_response: Optional[requests.Response] = None
        self.last_url: Optional[str] = None
        self._app_versions: Optional[List[Dict]] = None
        self._widget_schemas: Optional[List[Dict]] = None

        if check_certificates is None:
            check_certificates = env.bool(
                KechainEnv.KECHAIN_CHECK_CERTIFICATES, default=True
            )

        if check_certificates is False:
            self.session.verify = False

        # Retry implementation
        adapter = HTTPAdapter(
            max_retries=PykeRetry(
                total=RETRY_TOTAL,
                connect=RETRY_ON_CONNECTION_ERRORS,
                read=RETRY_ON_READ_ERRORS,
                redirect=RETRY_ON_REDIRECT_ERRORS,
                backoff_factor=RETRY_BACKOFF_FACTOR,
            )
        )
        self.session.mount("https://", adapter=adapter)
        self.session.mount("http://", adapter=adapter)

    def __del__(self):
        """Destroy the client object."""
        self.session.close()
        del self.session
        del self.auth
        del self.headers

    def __repr__(self):  # pragma: no cover
        return f"<pyke Client '{self.api_root}'>"

    @classmethod
    def from_env(
        cls,
        env_filename: Optional[str] = None,
        check_certificates: Optional[bool] = None,
    ) -> "Client":
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
            check_certificates = env.bool(
                KechainEnv.KECHAIN_CHECK_CERTIFICATES, default=True
            )
        client = cls(
            url=env(KechainEnv.KECHAIN_URL), check_certificates=check_certificates
        )

        if env(KechainEnv.KECHAIN_TOKEN, None):
            client.login(token=env(KechainEnv.KECHAIN_TOKEN))
        elif env(KechainEnv.KECHAIN_USERNAME, None) and env(
            KechainEnv.KECHAIN_PASSWORD, None
        ):
            client.login(
                username=env(KechainEnv.KECHAIN_USERNAME),
                password=env(KechainEnv.KECHAIN_PASSWORD),
            )

        return client

    def login(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
    ) -> None:
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
            self.headers["Authorization"] = f"Token {token}"
            self.auth = None
        elif username and password:
            self.headers.pop("Authorization", None)
            self.auth = (username, password)

    def _build_url(self, resource: str, **kwargs) -> str:
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
        users_url = self._build_url("users")
        response = self._request("GET", users_url)
        users = response.json()
        return users

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Perform the request on the API.

        It includes a default ForbiddenError check if the response came back as a 403.
        It stores the `last_response`, `last_request` and `last_url` on the Client object for
        debugging reasons.

        :param method: the HTTP method or GET, POST, PUT, PATCH, DELETE
        :param url: the url to call
        :param kwargs: additional arguments such as `params` (query params) and `json` data.
        :raises ForbiddenError: If the user is forbidden to perform the URL call.
        :returns: Response
        """
        self.last_request = None
        if method in ("PUT", "POST", "DELETE"):
            kwargs[
                "allow_redirects"
            ] = False  # to prevent redirects on write action. Better check your URL first.
        self.last_response = self.session.request(
            method, url, auth=self.auth, headers=self.headers, **kwargs
        )
        self.last_request = self.last_response.request
        self.last_url = self.last_response.url

        if self.last_response.status_code == requests.codes.forbidden:
            raise ForbiddenError(self.last_response.json()["results"][0])

        return self.last_response

    @property
    def app_versions(self) -> List[Dict]:
        """List of the versions of the internal KE-chain 'app' modules."""
        if not self._app_versions:
            app_versions_url = self._build_url("versions")

            response = self._request("GET", app_versions_url)

            if response.status_code == requests.codes.not_found:
                self._app_versions = []
            elif response.status_code == requests.codes.forbidden:
                raise ForbiddenError(response.json()["results"][0]["detail"])
            elif response.status_code != requests.codes.ok:
                raise APIError("Could not retrieve app versions", response=response)
            else:
                self._app_versions = response.json().get("results")

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
        if self.match_app_version(label="pim", version="<3.0.0"):
            raise NotImplementedError(
                "Widget schemas is not implemented in KE-chain versions lower that 3.0"
            )
        if not self._widget_schemas:
            response = self._request("GET", self._build_url("widgets_schemas"))
            if response.status_code != requests.codes.ok:  # pragma: no cover
                raise APIError("Could not retrieve widgets schemas.", response=response)
            self._widget_schemas = response.json().get("results")

        return self._widget_schemas

    def widget_schema(self, widget_type: str) -> Dict:
        """Widget schema for widget type.

        ..versionadded:: 3.0

        :param widget_type: Type of the widget to return the widgetschema for.
        :type widget_type: basestring
        :returns: dictionary with jsonschema to validate the widget meta
        :rtype: dict
        :raises APIError: When it could not retrieve the jsonschema from KE-chain
        :raises NotFoundError: When it could not find the correct schema
        """
        check_enum(widget_type, WidgetTypes, "widget_type")

        found = find(
            self.widget_schemas, lambda ws: ws.get("widget_type") == widget_type
        )
        if not found:
            raise NotFoundError(
                f"Could not find a widget_schema for widget_type: `{widget_type}`"
            )
        return found

    def match_app_version(
        self,
        app: Optional[str] = None,
        label: Optional[str] = None,
        version: Optional[str] = None,
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
            target_app = [
                a
                for a in self.app_versions
                if a.get("app") == app or a.get("label") == label
            ]
            if not target_app and not isinstance(default, bool):
                raise NotFoundError("Could not find the app or label provided")
            elif not target_app and isinstance(default, bool):
                return default
        else:
            raise IllegalArgumentError("Please provide either app or label")

        if not version:
            raise IllegalArgumentError(
                "Please provide semantic version string including operand eg: `>=1.0.0`"
            )

        app_version = target_app[0].get("version")

        if target_app and app_version and version:
            import semver

            return semver.Version.parse(app_version).match(version)
        elif not app_version:
            if isinstance(default, bool):
                return default
            else:
                raise NotFoundError(
                    "No version found on the app '{}'".format(target_app[0].get("app"))
                )

    def reload(
        self, obj: Base, url: Optional[str] = None, extra_params: Optional[Dict] = None
    ):
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
        check_type(value=obj, cls=Base, key="obj")
        url = check_text(text=url, key="url")
        extra_params = check_type(extra_params, dict, "extra_params")

        if url:
            url = url
        elif obj._json_data.get("url"):
            url = obj._json_data.get("url")
        else:
            # No known URL to reload the object: Try to build the url from the
            # class name (in lower case)

            extra_api_params = dict()
            superclasses = (
                obj.__class__.mro()
            )  # method resolution order, i.e. the obj's class and its superclasses
            for cls in superclasses:
                resource = cls.__name__.lower()
                stripped = resource.replace("2", "")

                try:
                    # set the id from the `obj.id` which is normally a keyname
                    # `<class_name>_id` (without the '2' if so)
                    url = self._build_url(
                        resource=resource, **{f"{stripped}_id": obj.id}
                    )
                    extra_api_params = API_EXTRA_PARAMS.get(resource)
                    break
                except KeyError:
                    if resource != stripped:
                        # Try again with stripped resource name
                        try:
                            url = self._build_url(
                                resource=stripped, **{f"{stripped}_id": obj.id}
                            )
                            extra_api_params = API_EXTRA_PARAMS.get(stripped)
                            break
                        except KeyError:
                            continue
                    else:
                        # If the resource was not recognized, try the next superclass
                        continue

            if url is None:
                raise IllegalArgumentError(
                    f'Provide URL to reload the "{obj}" object (could not identify the API'
                    " resource)."
                )

            # add the additional API params to the already provided extra params if they are provided.
            extra_params = (
                extra_params.update(**extra_api_params)
                if extra_params
                else extra_api_params
            )

        response = self._request("GET", url, params=extra_params)
        data = response.json().get("results", [])

        if response.status_code != requests.codes.ok or not len(data) > 0:
            raise NotFoundError(
                f"Could not reload {obj.__class__.__name__} {obj}", response=response
            )

        return obj.__class__(data[0], client=self)

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
        kwargs["limit"] = kwargs.get("limit", 2)
        results = method(*args, **kwargs)

        criteria = f"\nargs: {args}\nkwargs: {kwargs}"

        if len(results) == 0:
            raise NotFoundError(f"No {method.__name__} fit criteria:{criteria}")
        if len(results) != 1:
            raise MultipleFoundError(
                f"Multiple {method.__name__} fit criteria:{criteria}"
            )

        return results[0]

    def scopes(
        self,
        name: Optional[str] = None,
        pk: Optional[str] = None,
        status: Optional[Union[ScopeStatus, str]] = ScopeStatus.ACTIVE,
        **kwargs,
    ) -> List[Scope]:
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
            "status": check_enum(status, ScopeStatus, "status"),
        }
        name = check_text(text=name, key="name")
        pk = check_uuid(pk)

        if name:
            request_params["name"] = name
        if pk:
            request_params["id"] = pk

        request_params.update(API_EXTRA_PARAMS["scope"])
        url = self._build_url("scopes")

        if kwargs:
            request_params.update(**kwargs)

        response = self._request("GET", url=url, params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve Scopes", response=response)

        data = response.json()

        return [Scope(s, client=self) for s in data["results"]]

    def scope(self, *args, **kwargs) -> Scope:
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
        name: Optional[str] = None,
        pk: Optional[str] = None,
        scope: Optional[str] = None,
        **kwargs,
    ) -> List[Activity]:
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
            "id": check_uuid(pk),
            "name": check_text(text=name, key="name"),
            "scope_id": check_base(scope, Scope, "scope"),
        }

        request_params.update(API_EXTRA_PARAMS["activity"])

        if kwargs:
            request_params.update(**kwargs)

        response = self._request(
            "GET", self._build_url("activities"), params=request_params
        )

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve Activities", response=response)

        data = response.json()
        return [Activity(a, client=self) for a in data["results"]]

    def activity(self, *args, **kwargs) -> Activity:
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
        name: Optional[str] = None,
        pk: Optional[str] = None,
        model: Optional[Part] = None,
        category: Optional[Union[Category, str]] = Category.INSTANCE,
        scope_id: Optional[str] = None,
        parent: Optional[str] = None,
        activity: Optional[str] = None,
        widget: Optional[str] = None,
        limit: Optional[int] = None,
        batch: Optional[int] = PARTS_BATCH_LIMIT,
        **kwargs,
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
        # if limit is provided and the batchsize is bigger than the limit, ensure that the
        # batch size is maximised
        if limit and limit < batch:
            batch = limit

        request_params = dict(
            id=check_uuid(pk),
            name=check_text(text=name, key="name"),
            category=check_enum(category, Category, "category"),
            activity_id=check_base(activity, Activity, "activity"),
            widget_id=check_base(widget, Widget, "widget"),
            limit=batch,
            scope_id=check_uuid(scope_id),
            parent_id=check_base(parent, Part, "parent"),
            model_id=check_base(model, Part, "model"),
        )
        url = self._build_url("parts")
        request_params.update(API_EXTRA_PARAMS["parts"])

        if kwargs:
            request_params.update(**kwargs)

        response = self._request("GET", url, params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve Parts", response=response)

        data = response.json()

        part_results = data["results"]

        if batch and data.get("next"):
            while data["next"]:
                # respect the limit if set to > 0
                if limit and len(part_results) >= limit:
                    break
                response = self._request("GET", data["next"])
                data = response.json()
                part_results.extend(data["results"])

        return PartSet(Part(p, client=self) for p in part_results)

    def part(self, *args, **kwargs) -> Part:
        """Retrieve single KE-chain part.

        Uses the same interface as the :func:`parts` method but returns only a single pykechain
        :class:`models.Part` instance.

        If additional `keyword=value` arguments are provided, these are added to the request
        parameters. Please refer to the documentation of the KE-chain API for additional query
        parameters.

        When only the `pk` is provided as an input for the part search, the
        detail route will be called.

        :return: a single :class:`models.Part`
        :raises NotFoundError: When no `Part` is found
        :raises MultipleFoundError: When more than a single `Part` is found
        """
        part_id = None
        if len(args) >= 2:
            # the 2nd arg (index 1) is the pk
            part_id = check_uuid(args[1])
        elif "pk" in kwargs:
            part_id = check_uuid(kwargs.pop("pk"))
        elif "id" in kwargs:
            # for accidental use of 'id' on the part retrieving we have this smart
            # popper from the kwargs to ensure that the intention is still correct
            # it will result in a single Part retrieve.
            part_id = check_uuid(kwargs.pop("id"))

        if part_id:
            url = self._build_url("part", part_id=part_id)
            request_params = API_EXTRA_PARAMS["part"]

            response = self._request("GET", url, params=request_params)
            if response.status_code != requests.codes.ok:  # pragma: no cover
                raise NotFoundError("Could not retrieve Part", response=response)

            data = response.json()
            part_results = data["results"][0]
            return Part(part_results, client=self)

        return self._retrieve_singular(self.parts, *args, **kwargs)

    def model(self, *args, **kwargs) -> Part:
        """Retrieve single KE-chain part model.

        Uses the same interface as the :func:`part` method but returns only a single pykechain
        :class:`models.Part` instance of category `MODEL`.

        If additional `keyword=value` arguments are provided, these are added to the request
        parameters. Please refer to the documentation of the KE-chain API for additional query
        parameters.

        When only the `id` or `pk` is provided, the detail route for the part id will be
        called.

        :return: a single :class:`models.Part`
        :raises NotFoundError: When no `Part` is found
        :raises MultipleFoundError: When more than a single `Part` is found
        """
        kwargs["category"] = Category.MODEL
        return self.part(*args, **kwargs)

    def properties(
        self,
        name: Optional[str] = None,
        pk: Optional[str] = None,
        category: Optional[Union[Category, str]] = Category.INSTANCE,
        **kwargs,
    ) -> List["AnyProperty"]:
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
            "name": check_text(text=name, key="name"),
            "id": check_uuid(pk),
            "category": check_enum(category, Category, "category"),
        }
        if kwargs:  # pragma: no cover
            request_params.update(**kwargs)

        request_params.update(API_EXTRA_PARAMS["properties"])
        response = self._request(
            "GET", self._build_url("properties"), params=request_params
        )

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve Properties", response=response)

        return [Property.create(p, client=self) for p in response.json()["results"]]

    def property(self, *args, **kwargs) -> "AnyProperty":  # noqa: F
        """Retrieve single KE-chain Property.

        Uses the same interface as the :func:`properties` method but returns only a single
        pykechain :class:`models.Property` instance.

        If additional `keyword=value` arguments are provided, these are added to the request
        parameters. Please refer to the documentation of the KE-chain API for additional query
        parameters.

        When only the `pk` is provided as an input for the part search, the detail route will
        be called.

        :return: a single :class:`models.Property`
        :raises NotFoundError: When no `Property` is found
        :raises MultipleFoundError: When more than a single `Property` is found
        """
        property_id = None
        if len(args) >= 2:
            # the 2nd arg (index 1) is the pk
            property_id = check_uuid(args[1])
        elif "pk" in kwargs:
            property_id = check_uuid(kwargs.pop("pk"))
        elif "id" in kwargs:
            # for accidental use of 'id' on the part retrieving we have this smart
            # popper from the kwargs to ensure that the intention is still correct
            # it will result in a single Part retrieve.
            property_id = check_uuid(kwargs.pop("id"))

        if property_id:
            url = self._build_url("property", property_id=property_id)
            request_params = API_EXTRA_PARAMS["property"]

            response = self._request("GET", url, params=request_params)
            if response.status_code != requests.codes.ok:  # pragma: no cover
                raise NotFoundError("Could not retrieve Property", response=response)

            data = response.json()
            property_results = data["results"][0]
            return Property.create(property_results, client=self)
        return self._retrieve_singular(self.properties, *args, **kwargs)

    def services(
        self,
        name: Optional[str] = None,
        pk: Optional[str] = None,
        scope: Optional[str] = None,
        **kwargs,
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
            "name": check_text(text=name, key="name"),
            "id": check_uuid(pk),
            "scope": scope,
        }
        request_params.update(API_EXTRA_PARAMS["service"])

        if kwargs:
            request_params.update(**kwargs)

        response = self._request(
            "GET", self._build_url("services"), params=request_params
        )

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve Services", response=response)

        return [Service(service, client=self) for service in response.json()["results"]]

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
        name: Optional[str] = None,
        pk: Optional[str] = None,
        scope: Optional[str] = None,
        service: Optional[str] = None,
        **kwargs,
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
            "name": check_text(text=name, key="name"),
            "id": check_uuid(pk),
            "service": service,
            "scope": scope,
        }
        if kwargs:
            request_params.update(**kwargs)

        response = self._request(
            "GET", self._build_url("service_executions"), params=request_params
        )

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError(
                "Could not retrieve Service Executions", response=response
            )

        return [
            ServiceExecution(service_execution, client=self)
            for service_execution in response.json()["results"]
        ]

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

    def users(
        self, username: Optional[str] = None, pk: Optional[str] = None, **kwargs
    ) -> List[User]:
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
            "username": check_text(text=username, key="username"),
            "id": check_type(pk, (str, int), "pk"),
        }
        if kwargs:
            request_params.update(**kwargs)

        response = self._request("GET", self._build_url("users"), params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve Users", response=response)

        return [User(user, client=self) for user in response.json()["results"]]

    def user(self, *args, **kwargs) -> User:
        """
        User of KE-chain.

        Provides single user of :class:`User` of KE-chain. You can filter on username or id or an advanced filter.

        :param kwargs: Additional filtering keyword=value arguments
        :return: List of :class:`User`
        :raises NotFoundError: when a user could not be found
        :raises MultipleFoundError: when more than a single user can be found
        """
        return self._retrieve_singular(self.users, *args, **kwargs)

    def current_user(self) -> User:
        """
        Retrieve the User object logged in to the Client.

        :raises APIError if not logged in yet.
        :raises NotFoundError if user could not be found.
        :returns User
        :rtype User
        """
        try:
            response = self._request(
                method="GET", url=self._build_url(resource="user_current")
            )
        except Exception as e:
            raise APIError(
                f"No authentication provided to retrieve the current user:\n{e.args[0]}"
            )

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve current User", response=response)

        return User(response.json()["results"][0], client=self)

    def create_user(
        self,
        username: str,
        email: str,
        name: Optional[str] = None,
        team_ids: Optional[Union[Team, ObjectID]] = None,
        timezone: Optional[str] = None,
        language_code: Optional[LanguageCodes] = None,
        send_passwd_link: bool = False,
        **kwargs,
    ) -> "User":
        """Create a new User in KE-chain.

        The user is created in KE-chain. It is highly encouraged to provide a name
        for the user. Optionally one may choose to send out a forgot password
        link to the newly created user.

        :param username: username of the user
        :param email: email of the user
        :param name: (optional) full human name of the user
        :param team_ids: (optional) list of Team or Team id's to which the user should be added.
        :param language_code: (optional) the Language of the user. One of LanguageCodes. Eg. "nl"
        :param timezone: (optional) the timezone name of the user. Eg. "Europe/Amsterdam"
        :param send_passwd_link: (optional) boolean to send out a password reset link after
            the user is created. Defaults to False.
        """
        request_payload = {
            "username": check_text(username, "username"),
            "email": check_text(email, "email"),
            "name": check_text(name, "name"),
            "timezone": check_text(timezone, "timezone"),
            "language_code": check_enum(language_code, LanguageCodes, "language"),
            "team_ids": check_list_of_base(team_ids, Team, "team_ids") or [],
        }
        if kwargs:
            request_payload.update(**kwargs)

        response = self._request("POST", self._build_url("users"), json=request_payload)

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not create a new user", response=response)

        user = User(response.json()["results"][0], client=self)
        if send_passwd_link:
            user.reset_password()

        return user

    def teams(
        self,
        name: Optional[str] = None,
        pk: Optional[str] = None,
        is_hidden: Optional[bool] = False,
        **kwargs,
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
            "name": check_text(text=name, key="name"),
            "id": check_uuid(pk),
            "is_hidden": is_hidden,
        }
        if kwargs:
            request_params.update(**kwargs)

        response = self._request("GET", self._build_url("teams"), params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve Teams", response=response)

        return [Team(team, client=self) for team in response.json()["results"]]

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
        pk: Optional[str] = None,
        activity: Optional[Union[Activity, str]] = None,
        **kwargs,
    ) -> List[Widget]:
        """
        Widgets of an activity.

        Only works for KE-chain version 3.

        :param pk: (optional) the uuid of the widget.
        :type pk: basestring or None
        :param activity: (optional) the :class:`Activity` or UUID of the activity to filter the widgets for.
        :type activity: basestring or None
        :param kwargs: additional keyword arguments
        :return: A list of Widget objects
        :rtype: List
        :raises NotFoundError: when the widgets could not be found
        :raises APIError: when the API does not support the widgets, or when the API gives an error.
        """
        """Widgets of an activity."""
        request_params = dict(API_EXTRA_PARAMS["widgets"])
        request_params["id"] = check_uuid(pk)

        if isinstance(activity, Activity):
            request_params.update(dict(activity_id=activity.id))
        elif is_uuid(activity):
            request_params.update(dict(activity_id=activity))

        if kwargs:
            request_params.update(**kwargs)

        response = self._request(
            "GET", self._build_url("widgets"), params=request_params
        )

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve Widgets", response=response)

        return [
            Widget.create(json=json, client=self) for json in response.json()["results"]
        ]

    def widget(self, *args, **kwargs) -> Widget:
        """
        Retrieve a single widget.

        :return: Widget
        """
        return self._retrieve_singular(self.widgets, *args, **kwargs)

    #
    # Creators
    #

    def create_activity(
        self,
        parent: Union[Activity, str],
        name: str,
        activity_type: ActivityType = ActivityType.TASK,
        ref: Optional[str] = None,
        status: ActivityStatus = ActivityStatus.OPEN,
        description: Optional[str] = None,
        start_date: Optional[datetime.datetime] = None,
        due_date: Optional[datetime.datetime] = None,
        classification: ActivityClassification = None,
        tags: Optional[List[str]] = None,
        **kwargs,
    ) -> Activity:
        """
        Create a new activity.

        :param parent: parent under which to create the activity
        :type parent: basestring or :class:`models.Activity`
        :param name: new activity name
        :type name: basestring
        :param activity_type: type of activity: TASK (default) or PROCESS
        :type activity_type: basestring
        :param ref: activity ref, slug
        :type ref: basestring
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
        :return: the created :class:`models.Activity`
        :raises APIError: When the object could not be created
        :raises IllegalArgumentError: When an incorrect arguments are provided
        """
        if isinstance(parent, Activity):
            parent_classification = parent.classification
            parent_id = parent.id
        elif is_uuid(parent):
            parent_classification = None
            parent_id = parent
        else:
            raise IllegalArgumentError(
                f'`parent` must be an Activity or UUID, "{parent}" is neither'
            )

        if classification is None:
            if parent_classification is None:
                classification = ActivityClassification.WORKFLOW
            else:
                classification = parent_classification
        else:
            classification = check_enum(
                classification, ActivityClassification, "classification"
            )

        ref = check_text(ref, "ref")
        if ref:
            slug_ref = slugify_ref(ref)
            if slug_ref != ref:
                raise IllegalArgumentError(
                    "`ref` must be a slug, `{}` is not. "
                    "Use `slugify_ref` util function to convert to `{}`.".format(
                        ref, slug_ref
                    )
                )

        data = {
            "name": check_text(text=name, key="name"),
            "parent_id": parent_id,
            "status": check_enum(status, ActivityStatus, "status"),
            "activity_type": check_enum(activity_type, ActivityType, "activity_type"),
            "classification": classification,
            "description": check_text(text=description, key="description"),
            "start_date": check_datetime(dt=start_date, key="start_date"),
            "due_date": check_datetime(dt=due_date, key="due_date"),
            "tags": check_list_of_text(tags, key="tags", unique=True),
        }

        if ref:
            data["ref"] = slugify_ref(ref)

        if kwargs:
            data.update(kwargs)

        data = {k: v for k, v in data.items() if v is not None}

        response = self._request(
            "POST",
            self._build_url("activities"),
            json=data,
            params=API_EXTRA_PARAMS["activities"],
        )

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not create Activity.", response=response)

        new_activity = Activity(response.json()["results"][0], client=self)
        if isinstance(parent, Activity) and parent._cached_children is not None:
            parent._cached_children.append(new_activity)
        return new_activity

    def clone_activities(
        self,
        activities: List[Union[Activity, str]],
        activity_parent: Union[Activity, str],
        activity_update_dicts: Optional[Dict] = None,
        include_part_models: Optional[bool] = False,
        include_part_instances: Optional[bool] = False,
        include_children: Optional[bool] = True,
        excluded_parts: Optional[List[str]] = None,
        part_parent_model: Optional[Union[Part, str]] = None,
        part_parent_instance: Optional[Union[Part, str]] = None,
        part_model_rename_template: Optional[str] = None,
        part_instance_rename_template: Optional[str] = None,
        asynchronous: Optional[bool] = False,
        **kwargs,
    ) -> List[Activity]:
        """
        Clone multiple activities.

        .. versionadded:: 3.7
           The bulk clone activities with parts API is included in KE-chain backend since version
           3.6.

        :param activities: list of Activity object or UUIDs
        :type activities: list
        :param activity_parent: parent Activity sub-process object or UUID
        :type activity_parent: Activity
        :param activity_update_dicts: (O) dict of dictionaries, each key-value combination relating to an activity
        to clone and a dict of new values to assign, e.g. `{activity.id: {"name": "Cloned activity"}}`
        :type activity_update_dicts: dict
        :param include_part_models: (O) whether to clone the data models configured in the activities, defaults to False
        :type include_part_models: bool
        :param include_part_instances: (O) whether to clone the part instances of the data model configured in the
            activities, defaults to True
        :type include_part_instances: bool
        :param include_children: (O) whether to clone child parts
        :type include_children: bool
        :param excluded_parts: (O) list of Part2 objects or UUIDs to exclude from being cloned,
            maintaining the original configuration of the widgets.
        :type excluded_parts: list
        :param part_parent_model: (O) parent Part object or UUID for the copied data model(s)
        :type part_parent_model: Part
        :param part_parent_instance: (O) parent Part object or UUID for the copied part instance(s)
        :type part_parent_instance: Part
        :param part_model_rename_template: (O) renaming template for part models. Must contain "{name}"
        :type part_model_rename_template: str
        :param part_instance_rename_template: (O) renaming template for part instances. Must contain "{name}"
        :type part_instance_rename_template: str
        :param asynchronous: If true, immediately returns without activities (default = False)
        :type asynchronous: bool
        :return: list of cloned activities
        :rtype: list
        :raises APIError if cloned
        """
        if self.match_app_version(
            label="kechain2.core.pim", version=">=3.7.0"
        ):  # pragma: no cover
            raise APIError(
                "Cloning of activities with parts requires KE-chain version >= 3.7.0."
            )

        update_name = "activity_update_dicts"
        activity_ids = check_list_of_base(activities, cls=Activity, key="activities")
        update_dicts = (
            check_type(activity_update_dicts, dict, key=update_name) or dict()
        )

        if not all(key in activity_ids for key in update_dicts.keys()):
            incorrect_ids = [
                key for key in update_dicts.keys() if key not in activity_ids
            ]
            raise IllegalArgumentError(
                "The `{}` must contain updates to activities that are to be cloned. "
                "Did not recognize the following UUIDs:\n{}".format(
                    update_name, "\n".join(incorrect_ids)
                )
            )

        elif not all(isinstance(value, dict) for value in update_dicts.values()):
            raise IllegalArgumentError(f"The `{update_name}` must be a dict of dicts.")

        activities = [
            dict(id=uuid, **update_dicts.get(uuid, {})) for uuid in activity_ids
        ]

        data = dict(
            activity_parent_id=check_base(activity_parent, cls=Activity, key="parent"),
            include_part_models=check_type(include_part_models, bool, "clone_parts"),
            include_part_instances=check_type(
                include_part_instances, bool, "clone_part_instances"
            ),
            include_part_children=check_type(include_children, bool, "clone_children"),
            excluded_part_ids=check_list_of_base(
                excluded_parts, Part, "excluded_models"
            )
            or [],
            part_parent_model_id=check_base(
                part_parent_model, Part, "part_parent_model"
            ),
            part_parent_instance_id=check_base(
                part_parent_instance, Part, "part_parent_instance"
            ),
            part_models_rename_template=check_type(
                part_model_rename_template, str, "part_model_rename_template"
            ),
            part_instances_rename_template=check_type(
                part_instance_rename_template, str, "part_instance_rename_template"
            ),
            activities=activities,
        )

        if kwargs:
            data.update(kwargs)

        params = dict(API_EXTRA_PARAMS["activities"])
        params["async_mode"] = asynchronous

        response = self._request(
            "POST", self._build_url("activities_bulk_clone"), json=data, params=params
        )

        if (asynchronous and response.status_code != requests.codes.accepted) or (
            not asynchronous and response.status_code != requests.codes.created
        ):  # pragma: no cover
            raise APIError("Could not clone Activities.", response=response)

        cloned_activities = [
            Activity(d, client=self) for d in response.json()["results"]
        ]

        if isinstance(activity_parent, Activity):
            activity_parent._populate_cached_children(cloned_activities)

        return cloned_activities

    def update_activities(
        self,
        activities: List[Dict],
    ) -> None:
        """
        Update multiple activities in bulk.

        :param activities: list of dicts, each specifying the updated data per activity.
        :raises APIError
        :return: None
        """
        check_list_of_dicts(activities, "activities", fields=["id"])

        url = self._build_url("activities_bulk_update")
        response = self._request("PUT", url, json=activities)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Activities", response=response)

    def _create_part(self, action: str, data: Dict, **kwargs) -> Optional[Part]:
        """Create a part for PIM 2 internal core function."""
        # suppress_kevents should be in the data (not the query_params)
        if "suppress_kevents" in kwargs:
            data["suppress_kevents"] = kwargs.pop("suppress_kevents")

        # prepare url query parameters
        query_params = kwargs
        query_params.update(API_EXTRA_PARAMS["parts"])

        response = self._request(
            "POST", self._build_url(f"parts_{action}"), params=query_params, json=data
        )

        if response.status_code != requests.codes.created:
            raise APIError("Could not create Part", response=response)

        return Part(response.json()["results"][0], client=self)

    def create_part(
        self, parent: Part, model: Part, name: Optional[str] = None, **kwargs
    ) -> Part:
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
            raise IllegalArgumentError(
                "The `parent` and `model` should be 'Part' objects"
            )
        if parent.category != Category.INSTANCE:
            raise IllegalArgumentError("The `parent` should be of category 'INSTANCE'")
        if model.category != Category.MODEL:
            raise IllegalArgumentError("The `model` should be of category 'MODEL'")

        name = check_text(text=name, key="name") or model.name

        data = dict(name=name, parent_id=parent.id, model_id=model.id)
        return self._create_part(action="new_instance", data=data, **kwargs)

    def create_model(
        self,
        parent: Union[Part, str],
        name: str,
        multiplicity: Optional[Multiplicity] = Multiplicity.ZERO_MANY,
        **kwargs,
    ) -> Part:
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
        if isinstance(parent, Part):
            pass
        elif is_uuid(parent):
            parent = self.model(id=parent)
        else:
            raise IllegalArgumentError(
                f"`parent` should be either a parent part or a uuid, got '{parent}'"
            )

        if parent.category != Category.MODEL:
            raise IllegalArgumentError("The parent should be of category 'MODEL'")

        data = dict(
            name=check_text(name, "name"),
            parent_id=parent.id,
            multiplicity=check_enum(multiplicity, Multiplicity, "multiplicity"),
        )
        return self._create_part(action="create_child_model", data=data, **kwargs)

    def create_model_with_properties(
        self,
        parent: Union[Part, str],
        name: str,
        multiplicity: Optional[Multiplicity] = Multiplicity.ZERO_MANY,
        properties_fvalues: Optional[List[Dict]] = None,
        **kwargs,
    ) -> Part:
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
        :type parent: :class:`models.Part`
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
        if isinstance(parent, Part):
            pass
        elif is_uuid(parent):
            parent = self.model(id=parent)
        else:
            raise IllegalArgumentError(
                f"`parent` should be either a parent part or a uuid, got '{parent}'"
            )

        if parent.category != Category.MODEL:
            raise IllegalArgumentError("`parent` should be of category 'MODEL'")

        data = dict(
            name=check_text(text=name, key="name"),
            parent_id=parent.id,
            multiplicity=check_enum(multiplicity, Multiplicity, "multiplicity"),
            category=Category.MODEL,
            properties_fvalues=check_list_of_dicts(
                properties_fvalues, "properties_fvalues", ["name", "property_type"]
            ),
        )

        return self._create_part(action="create_child_model", data=data, **kwargs)

    def _create_clone(
        self,
        parent: Part,
        part: Part,
        name: Optional[str] = None,
        multiplicity: Optional[Multiplicity] = None,
        **kwargs,
    ) -> Part:
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
        check_type(part, Part, "part")
        check_type(parent, Part, "parent")

        data = dict(
            name=check_text(name, "name") or f"CLONE - {part.name}",
            suppress_kevents=kwargs.pop("suppress_kevents", None),
        )

        if part.category == Category.MODEL:
            data.update(
                {
                    "multiplicity": check_enum(
                        multiplicity, Multiplicity, "multiplicity"
                    )
                    or part.multiplicity,
                    "model_id": part.id,
                    "parent": parent.id,
                }
            )
        else:
            data.update({"instance_id": part.id, "parent_id": parent.id})

        if part.category == Category.MODEL:
            select_action = "clone_model"
        else:
            select_action = "clone_instance"

        query_params = kwargs
        query_params.update(API_EXTRA_PARAMS["parts"])
        url = self._build_url(f"parts_{select_action}")

        response = self._request("POST", url, params=query_params, data=data)

        if response.status_code != requests.codes.created:
            raise APIError("Could not clone Part", response=response)

        return Part(response.json()["results"][0], client=self)

    def create_proxy_model(
        self,
        model: Part,
        parent: Part,
        name: str,
        multiplicity: Optional[Multiplicity] = Multiplicity.ZERO_MANY,
        **kwargs,
    ) -> Part:
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
        check_type(model, Part, "model")
        check_type(parent, Part, "parent")

        if model.category != Category.MODEL:
            raise IllegalArgumentError("The model should be of category MODEL")
        if parent.category != Category.MODEL:
            raise IllegalArgumentError("The parent should be of category MODEL")

        data = dict(
            name=check_text(text=name, key="name"),
            model_id=model.id,
            parent_id=parent.id,
            multiplicity=check_enum(multiplicity, Multiplicity, "multiplicity"),
        )
        return self._create_part(action="create_proxy_model", data=data, **kwargs)

    def _create_parts_bulk(
        self,
        parts: List[Dict],
        asynchronous: Optional[bool] = False,
        retrieve_instances: Optional[bool] = True,
        **kwargs,
    ) -> PartSet:
        """
        Create multiple part instances simultaneously.

        :param parts: list of dicts, each specifying a part instance. Available fields per dict:
            :param name: (optional) name provided for the new instance as string otherwise use the name of the model
            :type name: basestring or None
            :param model_id: model of the part which to add new instances, should follow the model tree in KE-chain
            :type model_id: UUID
            :param parent_id: parent where to add new instances, should follow the model tree in KE-chain
            :type parent_id: UUID
            :param properties: list of dicts, each specifying a property to update. Available fields per dict:
                :param name: Name of the property model
                :type name: basestring
                :param value: The value of the Property instance after it is created
                :type value: basestring or int or bool or list (depending on the PropertyType)
                :param model_id: model of the property should follow the model tree in KE-chain
                :type model_id: UUID
            :type properties: list
        :type parts: list
        :param asynchronous: If true, immediately returns without parts (default = False)
        :type asynchronous: bool
        :param retrieve_instances: If true, will retrieve the created Part Instances in a PartSet
        :type retrieve_instances: bool
        :param kwargs:
        :return: list of Part instances or list of part UUIDs
        :rtype list
        """
        check_list_of_dicts(
            parts,
            "parts",
            [
                "name",
                "parent_id",
                "model_id",
                "properties",
            ],
        )
        for part in parts:
            check_list_of_dicts(
                part.get("properties"),
                "properties",
                [
                    "name",
                    "value",
                    "model_id",
                ],
            )

        parts = {"parts": parts}
        # prepare url query parameters
        query_params = kwargs
        query_params.update(API_EXTRA_PARAMS["parts"])
        query_params["async_mode"] = asynchronous

        response = self._request(
            "POST",
            self._build_url("parts_bulk_create"),
            params=query_params,
            json=parts,
        )

        if (asynchronous and response.status_code != requests.codes.accepted) or (
            not asynchronous and response.status_code != requests.codes.created
        ):  # pragma: no cover
            raise APIError(
                f"Could not create Parts. ({response.status_code})", response=response
            )

        part_ids = response.json()["results"][0]["parts_created"]
        if retrieve_instances:
            instances_per_id = dict()
            for part_ids_chunk in get_in_chunks(lst=part_ids, chunk_size=50):
                instances_per_id.update(
                    {
                        p.id: p for p in self.parts(id__in=",".join(part_ids_chunk))
                    }  # `id__in` does not guarantee order
                )
            part_instances = [
                instances_per_id[pk] for pk in part_ids
            ]  # Ensures order of parts wrt request
            return PartSet(parts=part_instances)
        return part_ids

    def _delete_parts_bulk(
        self,
        parts: List[Union[Part, str]],
        asynchronous: Optional[bool] = False,
        **kwargs,
    ) -> bool:
        """Delete multiple Parts simultaneously.

        :param parts: list of Part objects or UUIDs
        :type parts: List[Property] or List[UUID]
        :param asynchronous: If true, immediately returns (default = False)
        :type asynchronous: bool
        :param kwargs:
        :return: True if parts are delete successfully
        :raises APIError: if the parts could not be deleted
        :raises IllegalArgumentError: if there were neither Parts nor UUIDs in the list of parts
        """
        check_type(asynchronous, bool, "asynchronous")

        list_parts = list()
        for part in parts:
            if isinstance(part, Part):
                list_parts.append(part.id)
            elif is_uuid(part):
                list_parts.append(part)
            else:
                raise IllegalArgumentError(f"{part} is not a Part nor an UUID")
        payload = {"parts": list_parts}
        query_params = kwargs
        query_params.update(API_EXTRA_PARAMS["parts"])
        query_params["async_mode"] = asynchronous
        response = self._request(
            "DELETE",
            self._build_url("parts_bulk_delete"),
            params=query_params,
            json=payload,
        )
        # TODO - remove requests.codes.ok when async is implemented in the backend
        if (
            asynchronous
            and response.status_code not in (requests.codes.ok, requests.codes.accepted)
        ) or (
            not asynchronous
            and response.status_code not in (requests.codes.ok, requests.codes.accepted)
        ):  # pragma: no cover
            raise APIError(
                f"Could not delete Parts. ({response.status_code})", response=response
            )
        return True

    def create_property(
        self,
        model: Part,
        name: str,
        description: Optional[str] = None,
        property_type: Optional[Union[PropertyType, str]] = PropertyType.CHAR_VALUE,
        default_value: Optional[Any] = None,
        unit: Optional[str] = None,
        options: Optional[Dict] = None,
        **kwargs,
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
        check_enum(property_type, PropertyType, "property_type")
        check_type(model, Part, "model")
        if model.category != Category.MODEL:
            raise IllegalArgumentError("`model` should be of category MODEL")

        options = check_type(options, dict, "options") or dict()

        if (
            property_type
            in (PropertyType.REFERENCE_VALUE, PropertyType.REFERENCES_VALUE)
            and default_value
        ):
            # References only accept a single 'model_id' in the default value, we need to convert
            # this to a single value from the list of values.
            if isinstance(default_value, (list, tuple)):
                default_value = default_value[0]

            # Retrieve the referenced Scope from the default value
            if isinstance(default_value, Part):
                scope_options = dict(scope_id=default_value._json_data["scope_id"])
                default_value = [default_value.id]
            elif is_uuid(default_value):
                scope_options = dict(
                    scope_id=self.model(id=default_value)._json_data["scope_id"]
                )
                default_value = [default_value]
            else:
                raise IllegalArgumentError(
                    "Please provide a valid `default_value` being a `Part` of category `MODEL` "
                    "or a model uuid, got: '{}'".format(default_value)
                )
            options.update(scope_options)

        elif property_type == PropertyType.DATETIME_VALUE:
            default_value = check_datetime(dt=default_value, key="default_value")
        elif property_type == PropertyType.DATE_VALUE:
            default_value = check_date(dt=default_value, key="default_value")
        elif property_type == PropertyType.TIME_VALUE:
            default_value = check_time(dt=default_value, key="default_value")

        data = dict(
            name=check_text(name, "name"),
            part_id=model.id,
            description=check_text(description, "description") or "",
            property_type=property_type.upper(),
            value=default_value,
            unit=unit or "",
            value_options=options,
        )
        url = self._build_url("properties_create_model")
        query_params = kwargs
        query_params.update(API_EXTRA_PARAMS["properties"])

        response = self._request("POST", url, params=query_params, json=data)

        if response.status_code != requests.codes.created:
            raise APIError("Could not create Property", response=response)

        prop = Property.create(response.json()["results"][0], client=self)

        model.properties.append(prop)

        return prop

    def create_service(
        self,
        name: str,
        scope: Scope,
        description: Optional[str] = None,
        version: Optional[str] = None,
        service_type: Optional[ServiceType] = ServiceType.PYTHON_SCRIPT,
        environment_version: Optional[
            ServiceEnvironmentVersion
        ] = ServiceEnvironmentVersion.PYTHON_3_12,
        run_as: Optional[ServiceScriptUser] = ServiceScriptUser.KENODE_USER,
        pkg_path: Optional[str] = None,
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
         :class:`pykechain.enums.ServiceEnvironmentVersion`), defaults to `PYTHON_3_8`
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
            name=check_text(name, "name"),
            scope=check_base(scope, Scope, "scope"),  # not scope_id!
            description=check_text(text=description, key="description") or "",
            script_type=check_enum(service_type, ServiceType, "service_type"),
            script_version=check_text(text=version, key="version") or "1.0",
            env_version=check_enum(
                environment_version, ServiceEnvironmentVersion, "environment_version"
            ),
            run_as=check_enum(run_as, ServiceScriptUser, "run_as"),
        )

        response = self._request("POST", self._build_url("services"), json=data)

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not create Service", response=response)

        service = Service(response.json().get("results")[0], client=self)

        if pkg_path:
            # upload the package / refresh of the service will be done in the upload function
            service.upload(pkg_path)

        return service

    def create_scope(
        self,
        name: str,
        status: Optional[ScopeStatus] = ScopeStatus.ACTIVE,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        start_date: Optional[datetime.datetime] = None,
        due_date: Optional[datetime.datetime] = None,
        team: Optional[Union[Team, str]] = None,
        **kwargs,
    ) -> Scope:
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
            "name": check_text(name, "name"),
            "status": check_enum(status, ScopeStatus, "status"),
            "text": check_text(description, "description"),
            "tags": check_list_of_text(tags, "tags", True),
            "start_date": check_datetime(dt=start_date, key="start_date"),
            "due_date": check_datetime(dt=due_date, key="due_date"),
            "team_id": check_base(team, Team, "team", method=self.team),
        }

        # injecting additional kwargs for those cases that you need to add extra options.
        data_dict.update(kwargs)

        url = self._build_url("scopes")
        query_params = API_EXTRA_PARAMS["scopes"]
        response = self._request("POST", url, params=query_params, data=data_dict)

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not create Scope", response=response)

        return Scope(response.json()["results"][0], client=self)

    def delete_scope(self, scope: Scope, asynchronous: Optional[bool] = True) -> bool:
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
        check_type(scope, Scope, "scope")

        query_options = {
            "async_mode": check_type(asynchronous, bool, "asynchronous"),
        }

        response = self._request(
            "DELETE",
            url=self._build_url("scope", scope_id=str(scope.id)),
            params=query_options,
        )

        if response.status_code != requests.codes.no_content:  # pragma: no cover
            raise APIError(f"Could not delete Scope {scope}", response=response)

        return True

    def clone_scope(
        self,
        source_scope: Scope,
        name: Optional[str] = None,
        status: Optional[ScopeStatus] = None,
        start_date: Optional[datetime.datetime] = None,
        due_date: Optional[datetime.datetime] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        team: Optional[Union[Team, str]] = None,
        scope_options: Optional[Dict] = None,
        asynchronous: Optional[bool] = False,
    ) -> Optional[Scope]:
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
        check_type(source_scope, Scope, "scope")
        check_type(scope_options, dict, "scope_options")

        start_date = start_date or source_scope.start_date
        due_date = due_date or source_scope.due_date
        tags = check_list_of_text(tags, "tags", True) or source_scope.tags
        data_dict = {
            "scope_id": source_scope.id,
            "name": check_text(name, "name") or f"CLONE - {source_scope.name}",
            "start_date": check_datetime(dt=start_date, key="start_date"),
            "due_date": check_datetime(dt=due_date, key="due_date"),
            "text": check_text(description, "description") or source_scope.description,
            "status": check_enum(status, ScopeStatus, "status"),
            "tags": tags,
            "scope_options": scope_options or dict(),
            "async_mode": asynchronous,
        }

        team = check_base(team, Team, "team", method=self.team)
        if team:
            data_dict["team_id"] = team

        url = self._build_url("scopes_clone")
        query_params = API_EXTRA_PARAMS["scopes"]
        response = self._request("POST", url, params=query_params, json=data_dict)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            if response.status_code == requests.codes.forbidden:
                raise ForbiddenError(
                    f"Forbidden to clone Scope {source_scope}", response=response
                )
            else:
                raise APIError(
                    f"Could not clone Scope {source_scope}", response=response
                )

        if asynchronous and response.status_code == requests.codes.accepted:
            return None
        elif response.status_code == requests.codes.created:

            cloned_scope = Scope(response.json()["results"][0], client=source_scope._client)

            # TODO work-around, some attributes are not (yet) in the KE-chain response.json()
            cloned_scope._tags = tags
            cloned_scope.start_date = start_date
            cloned_scope.due_date = due_date
            return cloned_scope
        else:
            raise APIError(
                f"Unexpected response. Could not clone Scope {source_scope}", response=response
            )

    def create_team(
        self,
        name: str,
        user: Union[str, int, User],
        description: Optional[str] = None,
        options: Optional[Dict] = None,
        is_hidden: Optional[bool] = False,
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
            raise IllegalArgumentError(
                "the `user` is not of a type `User`, a `username` or a user id"
            )

        data = dict(
            name=check_text(name, "name"),
            description=check_text(description, "description") or "",
            options=check_type(options, dict, "options") or dict(),
            is_hidden=check_type(is_hidden, bool, "is_hidden"),
        )

        url = self._build_url("teams")
        response = self._request("POST", url, json=data)

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not create Team", response=response)

        new_team = Team(json=response.json().get("results")[0], client=self)

        new_team.add_members([user], role=TeamRoles.OWNER)
        team_members = new_team.members()

        members_to_remove = [
            self.user(username=u.get("username"))
            for u in team_members
            if u.get("username") != user.username
        ]

        if members_to_remove:
            new_team.remove_members(members_to_remove)
            new_team.refresh()

        return new_team

    @staticmethod
    def _validate_widget(
        activity: Union[Activity, str],
        widget_type: Union[WidgetTypes, str],
        title: Optional[str],
        meta: Dict,
        order: Optional[int],
        parent: Optional[Union[Widget, str]],
        **kwargs,
    ) -> Dict:
        """Validate the format and content of the configuration of a widget."""
        if widget_type == WidgetTypes.PROGRESS:
            warnings.warn(
                "The progress widget is not available in KE-chain from June 2024 onwards.",
                DeprecationWarning,
            )
        data = dict(
            activity_id=check_base(activity, Activity, "activity"),
            widget_type=check_enum(widget_type, WidgetTypes, "widget_type"),
            meta=meta,
            parent_id=check_base(parent, Widget, "parent"),
        )

        title = check_text(title, "title")
        if title is not None and not title.strip():
            raise IllegalArgumentError("`title` can not be empty")
        if title:
            data["title"] = title

        check_type(order, int, "order")
        if order is not None:
            data["order"] = order

        if kwargs:
            data.update(**kwargs)

        return data

    @staticmethod
    def _validate_related_models(
        readable_models: List,
        writable_models: List,
        part_instance: Union[Part, str],
        parent_part_instance: Union[Part, str],
        **kwargs,
    ) -> Tuple[List, List, str, str]:
        """
        Verify the format and content of the readable and writable models.

        :param readable_models: list of Properties or UUIDs
        :param writable_models: list of Properties or UUIDs
        :param kwargs: option to insert "inputs" and "outputs", instead of new inputs.
        :return: Tuple with both input lists, now with only UUIDs
        :rtype Tuple[List, List]
        """
        if kwargs.get("inputs"):
            readable_models = kwargs.pop("inputs")
        if kwargs.get("outputs"):
            writable_models = kwargs.pop("outputs")

        readable_model_ids = (
            check_list_of_base(readable_models, Property, "readable_models") or []
        )
        writable_model_ids = (
            check_list_of_base(writable_models, Property, "writable_models") or []
        )
        part_instance_id = check_base(part_instance, Part, "part_instance")
        parent_part_instance_id = check_base(
            parent_part_instance, Part, "parent_part_instance"
        )

        return (
            readable_model_ids,
            writable_model_ids,
            part_instance_id,
            parent_part_instance_id,
        )

    def create_widget(
        self,
        activity: Union[Activity, str],
        widget_type: Union[WidgetTypes, str],
        meta: Dict,
        title: Optional[str] = None,
        order: Optional[int] = None,
        parent: Optional[Union[Widget, str]] = None,
        readable_models: Optional[List] = None,
        writable_models: Optional[List] = None,
        part_instance: Optional[Union[Part, str]] = None,
        parent_part_instance: Optional[Union[Part, str]] = None,
        **kwargs,
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
        :param part_instance: Part object or UUID to be used as instance of the widget
        :type part_instance: Part or UUID
        :param parent_part_instance: Part object or UUID to be used as parent of the widget
        :type parent_part_instance: Part or UUID
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
            **kwargs,
        )

        (
            readable_model_ids,
            writable_model_ids,
            part_instance_id,
            parent_part_instance_id,
        ) = self._validate_related_models(
            readable_models=readable_models,
            writable_models=writable_models,
            part_instance=part_instance,
            parent_part_instance=parent_part_instance,
            **kwargs,
        )

        # perform the call
        url = self._build_url("widgets")
        response = self._request(
            "POST", url, params=API_EXTRA_PARAMS["widgets"], json=data
        )

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not create Widget", response=response)

        # create the widget and do postprocessing
        manager = activity._widgets_manager if isinstance(activity, Activity) else None

        widget = Widget.create(
            json=response.json().get("results")[0], client=self, manager=manager
        )

        # update the associations if needed
        if readable_model_ids is not None or writable_model_ids is not None:
            widget.update_associations(
                readable_models=readable_model_ids,
                writable_models=writable_model_ids,
                part_instance=part_instance_id,
                parent_part_instance=parent_part_instance_id,
            )

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
                activity=widget.get("activity"),
                widget_type=widget.get("widget_type"),
                title=widget.get("title"),
                meta=widget.get("meta"),
                order=widget.get("order"),
                parent=widget.get("parent"),
                **widget.pop("kwargs", dict()),
            )
            bulk_data.append(data)

            bulk_associations.append(
                self._validate_related_models(
                    readable_models=widget.get("readable_models"),
                    writable_models=widget.get("writable_models"),
                    part_instance=widget.get("part_instance"),
                    parent_part_instance=widget.get("parent_part_instance"),
                    **widget.pop("kwargs", dict()),
                )
            )

        url = self._build_url("widgets_bulk_create")
        response = self._request(
            "POST", url, params=API_EXTRA_PARAMS["widgets"], json=bulk_data
        )

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not create Widgets", response=response)

        # create the widget and do postprocessing
        widgets = []
        for widget_response in response.json().get("results"):
            widget = Widget.create(json=widget_response, client=self)
            widgets.append(widget)

        self.update_widgets_associations(
            widgets=widgets, associations=bulk_associations, **kwargs
        )

        return widgets

    def update_widgets(self, widgets: List[Dict]) -> List[Widget]:
        """
        Bulk-update of widgets.

        :param widgets: list of widget configurations.
        :type widgets: List[Dict]
        :return: list of Widget objects
        :rtype List[Widget]
        """
        check_list_of_dicts(widgets, "widgets", fields=["id"])
        if len(widgets) != len({w.get("id") for w in widgets}):
            raise IllegalArgumentError(
                "`widgets` must be a list of dicts with one dict per widget, "
                "but found multiple dicts updating the same widget"
            )

        response = self._request(
            "PUT",
            self._build_url("widgets_bulk_update"),
            params=API_EXTRA_PARAMS["widgets"],
            json=widgets,
        )

        if response.status_code != requests.codes.ok:
            raise APIError("Could not update Widgets", response=response)

        widgets_response = response.json().get("results")
        return [
            Widget.create(json=widget_json, client=self)
            for widget_json in widgets_response
        ]

    def delete_widget(self, widget: Union[Widget, str]) -> None:
        """
        Delete a single Widget.

        :param widget: Widget or its UUID to be deleted
        :type widget: Widget or basestring
        :return: None
        :raises APIError: whenever the widget could not be deleted
        :raises IllegalArgumentError: whenever the input `widget` is invalid
        """
        widget = check_base(widget, Widget, "widget")
        url = self._build_url("widget", widget_id=widget)
        response = self._request("DELETE", url)

        if response.status_code != requests.codes.no_content:  # pragma: no cover
            raise APIError(f"Could not delete Widget {widget}", response=response)

    def delete_widgets(self, widgets: List[Union[Widget, str]]) -> None:
        """
        Delete multiple Widgets.

        :param widgets: List, Tuple or Set of Widgets or their UUIDs to be deleted
        :type widgets: List[Union[Widget, Text]]
        :return: None
        :raises APIError: whenever the widgets could not be deleted
        :raises IllegalArgumentError: whenever the input `widgets` is invalid
        """
        widget_ids = check_list_of_base(widgets, Widget, "widgets")

        data = [dict(id=pk) for pk in widget_ids]

        url = self._build_url("widgets_bulk_delete")
        response = self._request("DELETE", url, json=data)

        if response.status_code != requests.codes.no_content:
            raise APIError("Could not delete Widgets", response=response)

    @staticmethod
    def _validate_associations(
        widgets: List[Union[Widget, str]],
        associations: List[Tuple[List, List, Part, Part]],
    ) -> List[str]:
        """Perform the validation of the internal widgets and associations."""
        widget_ids = check_list_of_base(widgets, Widget, "widgets")

        if not isinstance(associations, List) and all(
            isinstance(a, tuple) and len(a) in [2, 4] for a in associations
        ):
            raise IllegalArgumentError(
                "`associations` must be a list of tuples, defining the readable and writable"
                " models per widget, and optionally the part and parent part instances"
            )

        if not len(widgets) == len(associations):
            raise IllegalArgumentError(
                "The `widgets` and `associations` lists must be of equal length, "
                "not {} and {}.".format(len(widgets), len(associations))
            )

        return widget_ids

    def associations(
        self,
        widget: Optional[Widget] = None,
        activity: Optional[Activity] = None,
        part: Optional[Part] = None,
        property: Optional[AnyProperty] = None,
        scope: Optional[Scope] = None,
        limit: Optional[int] = None,
    ) -> List[Association]:
        """
        Retrieve a list of associations.

        :param widget: widget for which to retrieve associations
        :type widget: Widget
        :param activity: activity for which to retrieve associations
        :type activity: Activity
        :param part: part for which to retrieve associations
        :type part: Part
        :param property: property for which to retrieve associations
        :type property: AnyProperty
        :param scope: scope for which to retrieve associations
        :type scope: Scope
        :param limit: maximum number of associations to retrieve
        :type limit: int
        :return: list of association objects
        :rtype List[Association]
        """
        part = check_type(part, Part, "part")
        if part is not None:
            if part.category == Category.MODEL:
                part_instance = ""
                part_model = part.id
            else:
                part_instance = part.id
                part_model = ""
        else:
            part_instance = ""
            part_model = ""

        prop = check_type(property, Property, "property")
        if prop is not None:
            if prop.category == Category.MODEL:
                property_model = prop.id
                property_instance = ""
            else:
                property_model = ""
                property_instance = prop.id
        else:
            property_instance = ""
            property_model = ""

        limit = check_type(limit, int, "limit") or ""
        if limit and limit < 1:
            raise IllegalArgumentError("`limit` is not a positive integer!")

        request_params = {
            "limit": limit,
            "widget": check_base(widget, Widget, "widget") or "",
            "activity": check_base(activity, Activity, "activity") or "",
            "scope": check_base(scope, Scope, "scope") or "",
            "instance_part": part_instance,
            "instance_property": property_instance,
            "model_part": part_model,
            "model_property": property_model,
        }

        url = self._build_url("associations")
        response = self._request("GET", url, params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not retrieve Associations", response=response)

        associations = [
            Association(json=r, client=self) for r in response.json()["results"]
        ]

        return associations

    def update_widget_associations(
        self,
        widget: Union[Widget, str],
        readable_models: Optional[List] = None,
        writable_models: Optional[List] = None,
        part_instance: Optional[Union[Part, str]] = None,
        parent_part_instance: Optional[Union[Part, str]] = None,
        **kwargs,
    ) -> None:
        """
        Update associations on this widget.

        This is a patch to the list list of associations. Existing associations are not replaced.

        :param widget: widget to update associations for
        :type widget: :class:`Widget` or UUID
        :param readable_models: list of property models (of :class:`Property` or property_ids (uuids) that has
                                   read rights
        :type readable_models: List[Property] or List[UUID] or None
        :param writable_models: list of property models (of :class:`Property` or property_ids (uuids) that has
                                   write rights
        :type writable_models: List[Property] or List[UUID] or None
        :param part_instance: Part object or UUID to be used as instance of the widget
        :type part_instance: Part or UUID
        :param parent_part_instance: Part object or UUID to be used as parent of the widget
        :type parent_part_instance: Part or UUID
        :return: None
        :raises APIError: when the associations could not be changed
        :raise IllegalArgumentError: when the list is not of the right type
        """
        self.update_widgets_associations(
            widgets=[widget],
            associations=[
                (
                    readable_models if readable_models else [],
                    writable_models if writable_models else [],
                    part_instance,
                    parent_part_instance,
                )
            ],
            **kwargs,
        )

    def update_widgets_associations(
        self, widgets: List[Union[Widget, str]], associations: List[Tuple], **kwargs
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
            if len(association) == 2:
                readable_models, writable_models = association
                part_instance, parent_part_instance = None, None
            else:
                (
                    readable_models,
                    writable_models,
                    part_instance,
                    parent_part_instance,
                ) = association

            (
                readable_model_ids,
                writable_model_ids,
                part_instance_id,
                parent_part_instance_id,
            ) = self._validate_related_models(
                readable_models=readable_models,
                writable_models=writable_models,
                part_instance=part_instance,
                parent_part_instance=parent_part_instance,
            )

            data = dict(
                id=widget_id,
            )

            if readable_model_ids:
                data.update(dict(readable_model_properties_ids=readable_model_ids))
            if writable_model_ids:
                data.update(dict(writable_model_properties_ids=writable_model_ids))
            if part_instance_id:
                data.update(dict(part_instance_id=part_instance_id))
            if parent_part_instance_id:
                data.update(dict(parent_part_instance_id=parent_part_instance_id))

            if kwargs:
                data.update(**kwargs)

            bulk_data.append(data)

        # perform the call
        url = self._build_url("widgets_update_associations")
        response = self._request(
            "PUT", url, params=API_EXTRA_PARAMS["widgets"], json=bulk_data
        )

        if response.status_code != requests.codes.ok:
            raise APIError("Could not update Associations", response=response)

        return None

    def set_widget_associations(
        self,
        widget: Union[Widget, str],
        readable_models: Optional[List] = None,
        writable_models: Optional[List] = None,
        part_instance: Optional[Union[Part, str]] = None,
        parent_part_instance: Optional[Union[Part, str]] = None,
        **kwargs,
    ) -> None:
        """
        Update associations on this widget.

        This is an absolute list of associations. If no property model id's are provided, then the associations are
        emptied out and replaced with no associations.

        :param widget: widget to set associations for.
        :type widget: :class:`Widget` or UUID
        :param readable_models: list of property models (of :class:`Property` or property_ids (uuids) that has
                                   read rights
        :type readable_models: List[Property] or List[UUID] or None
        :param writable_models: list of property models (of :class:`Property` or property_ids (uuids) that has
                                   write rights
        :type writable_models: List[Property] or List[UUID] or None
        :param part_instance: Part object or UUID to be used as instance of the widget
        :type part_instance: Part or UUID
        :param parent_part_instance: Part object or UUID to be used as parent of the widget
        :type parent_part_instance: Part or UUID
        :return: None
        :raises APIError: when the associations could not be changed
        :raise IllegalArgumentError: when the list is not of the right type
        """
        self.set_widgets_associations(
            widgets=[widget],
            associations=[
                (
                    readable_models,
                    writable_models,
                    part_instance,
                    parent_part_instance,
                )
            ],
            **kwargs,
        )

    def set_widgets_associations(
        self, widgets: List[Union[Widget, str]], associations: List[Tuple], **kwargs
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
            if len(association) == 2:
                readable_models, writable_models = association
                part_instance, parent_part_instance = None, None
            else:
                (
                    readable_models,
                    writable_models,
                    part_instance,
                    parent_part_instance,
                ) = association

            (
                readable_model_ids,
                writable_model_ids,
                part_instance_id,
                parent_part_instance_id,
            ) = self._validate_related_models(
                readable_models=readable_models,
                writable_models=writable_models,
                part_instance=part_instance,
                parent_part_instance=parent_part_instance,
            )

            data = dict(
                id=widget_id,
            )

            if readable_model_ids:
                data.update(dict(readable_model_properties_ids=readable_model_ids))
            if writable_model_ids:
                data.update(dict(writable_model_properties_ids=writable_model_ids))
            if part_instance_id:
                data.update(dict(part_instance_id=part_instance_id))
            if parent_part_instance_id:
                data.update(dict(parent_part_instance_id=parent_part_instance_id))

            if kwargs:  # pragma: no cover
                data.update(**kwargs)

            bulk_data.append(data)

        # perform the call
        url = self._build_url("widgets_set_associations")
        response = self._request(
            "PUT", url, params=API_EXTRA_PARAMS["widgets"], json=bulk_data
        )

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not set Associations", response=response)

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
        check_type(widget, Widget, "widget")

        # perform the call
        url = self._build_url("widget_clear_associations", widget_id=widget.id)
        response = self._request(method="PUT", url=url)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError(
                f"Could not clear Associations of Widget {widget}", response=response
            )

        return None

    def remove_widget_associations(
        self,
        widget: Widget,
        models: Optional[List[Union["AnyProperty", str]]] = (),
        **kwargs,
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
        check_type(widget, Widget, "widget")

        model_ids = check_list_of_base(models, Property, "models")

        if not model_ids:
            return

        data = dict(
            id=widget.id,
            model_properties_ids=model_ids,
        )

        # perform the call
        url = self._build_url("widget_remove_associations", widget_id=widget.id)
        response = self._request(
            method="PUT", url=url, params=API_EXTRA_PARAMS["widget"], json=data
        )

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError(
                f"Could not remove Associations of Widget {widget}", response=response
            )

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
        :raises IllegalArgumentError: if the 'parent' type is not :class:`Activity` or UUID
        :raises APIError: if an Error occurs.
        """
        activity = check_type(activity, Activity, "activity")

        if isinstance(parent, Activity):
            parent_object = parent
            parent_id = parent.id
        elif isinstance(parent, str) and is_uuid(parent):
            parent_id = parent
            parent_object = self.activity(id=parent)
        else:
            raise IllegalArgumentError(
                "Please provide either an activity object or a UUID"
            )

        if parent_object.activity_type != ActivityType.PROCESS:
            raise IllegalArgumentError(
                "One can only move an `Activity` under a subprocess."
            )

        update_dict = {
            "parent_id": parent_object.id,
            "classification": check_enum(
                classification, ActivityClassification, "classification"
            )
            or parent_object.classification,
        }

        url = self._build_url("activity_move", activity_id=str(activity.id))
        response = self._request("PUT", url, data=update_dict)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError(f"Could not move Activity {activity}", response=response)

        activity.parent_id = parent_id

    def update_properties(self, properties: List[Dict]) -> List["AnyProperty"]:
        """
        Update multiple properties simultaneously.

        :param properties: list of dictionaries to set the properties
        :type properties: List[Dict]
        :raises: IllegalArgumentError
        :return: list of Properties
        :rtype List[AnyProperty]


        Examples
        --------
        >>> properties = client.properties(limit=3)
        >>> update_dicts = [dict(id=p.id, value=p.value) for p in properties]
        >>> client.update_properties(properties=update_dicts)

        """
        check_list_of_dicts(properties, "properties")

        response = self._request(
            "POST",
            self._build_url("properties_bulk_update"),
            params=API_EXTRA_PARAMS["property"],
            json=properties,
        )

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Properties", response=response)

        properties = [
            Property.create(client=self, json=js) for js in response.json()["results"]
        ]

        return properties

    def notifications(self, pk: Optional[str] = None, **kwargs) -> List[Notification]:
        """Retrieve one or more notifications stored on the instance.

        If additional `keyword=value` arguments are provided, these are added to the request parameters. Please
        refer to the documentation of the KE-chain API for additional query parameters.

        :param pk: if provided, filter the search by notification_id
        :type pk: basestring or None
        :param kwargs: (optional) additional search keyword arguments
        :return: list of :class:`models.Notification` objects
        :raises APIError: When the retrieval call failed due to various reasons
        """
        request_params = {"id": check_uuid(pk)}

        if kwargs:
            request_params.update(**kwargs)

        response = self._request(
            "GET", self._build_url("notifications"), params=request_params
        )

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not retrieve Notifications", response=response)

        data = response.json()

        return [
            Notification(notification, client=self) for notification in data["results"]
        ]

    def notification(self, pk: Optional[str] = None, *args, **kwargs) -> Notification:
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

    def create_notification(
        self,
        subject: str,
        message: str,
        status: Optional[NotificationStatus] = NotificationStatus.DRAFT,
        recipients: Optional[List[Union[User, str]]] = None,
        team: Optional[Union[Team, str]] = None,
        from_user: Optional[Union[User, str]] = None,
        event: Optional[NotificationEvent] = None,
        channel: Optional[NotificationChannels] = NotificationChannels.EMAIL,
        **kwargs,
    ) -> Notification:
        """
        Create a single `Notification`.

        :param subject: Header text of the notification
        :type subject: str
        :param message: Content message of the notification
        :type message: str
        :param status: (O) life-cycle status of the notification, defaults to "DRAFT".
        :type status: NotificationStatus
        :param recipients: (O) list of recipients, each being a User object, user ID or an email address.
        :type recipients: list
        :param team: (O) team object to which the notification is constrained
        :type team: Team object or Team UUID
        :param from_user: (O) Sender of the notification, either a User object or user ID. Defaults to script user.
        :type from_user: User or user ID
        :param event: (O) originating event of the notification.
        :type event: NotificationEvent
        :param channel: (O) method used to send the notification, defaults to "EMAIL".
        :type channel: NotificationChannels
        :param kwargs: (optional) keyword=value arguments
        :return: the newly created `Notification`
        :raises: APIError: when the `Notification` could not be created
        """
        if from_user is None:
            from_user = self.current_user()

        recipient_users = list()
        recipient_emails = list()

        if recipients is not None:
            if isinstance(recipients, list) and all(
                isinstance(r, (str, int, User)) for r in recipients
            ):
                for recipient in recipients:
                    if is_valid_email(recipient):
                        recipient_emails.append(recipient)
                    else:
                        recipient_users.append(check_user(recipient, User, "recipient"))

            else:
                raise IllegalArgumentError(
                    "`recipients` must be a list of User objects, IDs or email addresses, "
                    '"{}" ({}) is not.'.format(recipients, type(recipients))
                )

        data = {
            "status": check_enum(status, NotificationStatus, "status"),
            "event": check_enum(event, NotificationEvent, "event"),
            "subject": check_text(subject, "subject"),
            "message": check_text(message, "message"),
            "recipient_users": recipient_users,
            "recipient_emails": recipient_emails,
            "team": check_base(team, Team, "team"),
            "from_user": check_user(from_user, User, "from_user"),
            "channels": [channel]
            if check_enum(channel, NotificationChannels, "channel")
            else [],
        }

        data.update(kwargs)
        data.update(API_EXTRA_PARAMS["notifications"])

        url = self._build_url("notifications")

        response = self._request("POST", url, data=data)

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not create Notification", response=response)

        notification = Notification(response.json().get("results")[0], client=self)
        return notification

    def delete_notification(self, notification: Union[Notification, str]) -> None:
        """
        Delete a single Notification.

        :param notification: Notification or its UUID to be deleted
        :type notification: Notification or basestring
        :return: None
        :raises APIError: whenever the notification could not be deleted
        :raises IllegalArgumentError: whenever the input `notification` is invalid
        """
        notification = check_base(notification, Notification, "notification")

        url = self._build_url("notification", notification_id=notification)
        response = self._request("DELETE", url)

        if response.status_code != requests.codes.no_content:  # pragma: no cover
            raise APIError(
                f"Could not delete Notification {notification}", response=response
            )

    def banners(
        self,
        pk: Optional[str] = None,
        text: Optional[str] = None,
        is_active: Optional[bool] = None,
        **kwargs,
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
            "text": check_text(text, "text"),
            "id": check_uuid(pk),
            "is_active": check_type(is_active, bool, "is_active"),
        }
        request_params.update(API_EXTRA_PARAMS["banners"])

        if kwargs:  # pragma: no cover
            request_params.update(**kwargs)

        response = self._request(
            "GET", self._build_url("banners"), params=request_params
        )

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve Banners", response=response)

        data = response.json()
        return [Banner(banner, client=self) for banner in data["results"]]

    def banner(self, *args, **kwargs) -> Banner:
        """
        Retrieve a single Banner, see `banners()` for available arguments.

        :return: single banner
        :rtype: Banner
        """
        return self._retrieve_singular(self.banners, *args, **kwargs)

    def create_banner(
        self,
        text: str,
        icon: str,
        active_from: datetime.datetime,
        active_until: Optional[datetime.datetime] = None,
        is_active: Optional[bool] = False,
        url: Optional[str] = None,
        **kwargs,
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
        :rtype: Banner
        """
        data = {
            "text": check_text(text, "text"),
            "icon": check_text(icon, "icon"),
            "active_from": check_datetime(active_from, "active_from"),
            "active_until": check_datetime(active_until, "active_until"),
            "is_active": check_type(is_active, bool, "is_active"),
            "url": check_url(url),
        }

        # prepare url query parameters
        query_params = kwargs
        query_params.update(API_EXTRA_PARAMS["banners"])

        response = self._request(
            "POST", self._build_url("banners"), params=query_params, json=data
        )

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not create Banner", response=response)

        return Banner(response.json()["results"][0], client=self)

    def active_banner(self) -> Banner:
        """
        Retrieve the currently active banner.

        :return: Banner object. If no banner is active, returns None.
        :rtype: Banner
        :raise APIError whenever the banners could not be retrieved properly.
        :raises NotFoundError whenever there is no active banner.
        :raises MultipleFoundError whenever multiple banners are active.
        """
        response = self._request("GET", self._build_url("banner_active"))

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve active Banner", response=response)

        active_banner_list = response.json()["results"]
        if not active_banner_list:
            raise NotFoundError("No current active banner.")
        elif len(active_banner_list) > 1:
            raise MultipleFoundError("There are multiple active banners.")
        else:
            data = active_banner_list[0]

        return Banner(json=data, client=self)

    def expiring_download(self, *args, **kwargs) -> ExpiringDownload:
        """Retrieve a single expiring download.

        :return: a single :class:`models.ExpiringDownload`
        :raises NotFoundError: When no `ExpiringDownload` is found
        :raises MultipleFoundError: When more than a single `ExpiringDownload` is found
        """
        return self._retrieve_singular(self.expiring_downloads, *args, **kwargs)

    def expiring_downloads(
        self, pk: Optional[str] = None, expires_in: Optional[int] = None, **kwargs
    ) -> List[ExpiringDownload]:
        """Search for Expiring Downloads with optional pk.

        :param pk: if provided, filter the search for an expiring download by download_id
        :type pk: basestring or None
        :param expires_in: if provided, filter the search for the expires_in (in seconds)
        :type expires_in: int
        :return: list of Expiring Downloads objects
        """
        request_params = {
            "id": check_uuid(pk),
            "expires_in": check_type(expires_in, int, "expires_in"),
        }
        request_params.update(API_EXTRA_PARAMS["expiring_downloads"])

        if kwargs:
            request_params.update(**kwargs)

        response = self._request(
            "GET", self._build_url("expiring_downloads"), params=request_params
        )

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError(
                "Could not retrieve Expiring Downloads", response=response
            )

        return [
            ExpiringDownload(json=download, client=self)
            for download in response.json()["results"]
        ]

    def create_expiring_download(
        self,
        expires_at: Optional[datetime.datetime] = None,
        expires_in: Optional[int] = None,
        content_path: Optional[str] = None,
    ) -> ExpiringDownload:
        """
        Create an new Expiring Download.

        :param expires_at: The moment at which the ExpiringDownload will expire
        :type expires_at: datetime.datetime
        :param expires_in: The amount of time (in seconds) in which the ExpiringDownload will expire
        :type expires_in: int
        :param content_path: the path to the file to be uploaded in the newly created `ExpiringDownload` object
        :type content_path: str
        :return:
        """
        expires_at = check_type(expires_at, datetime.datetime, "expires_at")
        data = dict(
            created_at=datetime.datetime.now().isoformat(),
            expires_at=expires_at.isoformat(),
            expires_in=expires_in,
        )
        response = self._request(
            "POST", self._build_url("expiring_downloads"), json=data
        )
        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not create Expiring Download", response=response)

        expiring_download = ExpiringDownload(
            response.json().get("results")[0], client=self
        )

        if content_path:
            expiring_download.upload(content_path)

        return expiring_download

    def create_context(
        self,
        name: str,
        context_type: ContextType,
        scope: Scope,
        context_group: ContextGroup = None,
        activities=None,
        description: str = None,
        tags=None,
        options=None,
        feature_collection=None,
        start_date=None,
        due_date=None,
        **kwargs,
    ) -> Context:
        """
        Create a new Context object of a ContextType in a scope.

        .. versionadded:: 3.12

        :param name: Name of the Context to be displayed to the end-user.
        :context_type: A type of Context, as defined in `ContextType` eg: STATIC_LOCATION, TIME_PERIOD
        :param scope: Scope object or Scope Id where the Context is active on.
        :param description: (optional) description of the Context
        :param activities: (optional) associated list of Activity or activity object ID
        :param context_group: (optional) context_group of the context. Choose from `ContextGroup` enumeration.
        :param tags: (optional) list of tags
        :param options: (optional) dictionary with options.
        :param feature_collection: (optional) dict with a geojson feature collection to store for a STATIC_LOCATION
        :param start_date: (optional) start datetime for a TIME_PERIOD context
        :param due_date: (optional) start datetime for a TIME_PERIOD context
        :return: a created Context Object
        :raises APIError: When the object cannot be created.
        """
        data = {
            "name": check_text(name, "name"),
            "description": check_text(description or "", "description"),
            "scope": check_base(scope, Scope, "scope"),
            "context_type": check_enum(context_type, ContextType, "context_type"),
            "tags": check_list_of_text(tags, "tags"),
            "context_group": check_enum(context_group, ContextGroup, "context_group"),
            "activities": check_list_of_base(activities, Activity, "activities"),
            "options": check_type(options, dict, "options"),
            "feature_collection": check_type(
                feature_collection, dict, "feature_collection"
            ),
            "start_date": check_datetime(start_date, "start_date"),
            "due_date": check_datetime(due_date, "due_date"),
        }

        if data["feature_collection"] is None:
            data["feature_collection"] = {}
        if data["activities"] is None:
            data["activities"] = []
        if data["options"] is None:
            data["options"] = {}

        # prepare url query parameters
        query_params = kwargs
        query_params.update(API_EXTRA_PARAMS["context"])

        response = self._request(
            "POST", self._build_url("contexts"), params=query_params, json=data
        )

        if response.status_code != requests.codes.created:
            raise APIError("Could not create Context", response=response)

        return Context(response.json()["results"][0], client=self)

    def delete_context(self, context: Context) -> None:
        """Delete the Context.

        .. versionadded:: 3.12

        :param context: The context object to delete
        """
        context = check_type(context, Context, "context")
        self._build_url("context", context_id=context.id)

        response = self._request(
            "DELETE", self._build_url("context", context_id=context.id)
        )

        if response.status_code != requests.codes.no_content:  # pragma: no cover
            raise APIError("Could not delete Contexts", response=response)

    def context(self, *args, **kwargs) -> Context:
        """
        Retrieve a single Context, see `contexts()` for available arguments.

        .. versionadded:: 3.12

        :return: a single Contexts
        :rtype: Context
        """
        return Context.get(client=self, **kwargs)
        # return self._retrieve_singular(self.contexts, *args, **kwargs)  # noqa

    def contexts(
        self,
        pk: Optional[ObjectID] = None,
        context_type: Optional[ContextType] = None,
        activities: Optional[List[Union[Activity, ObjectID]]] = None,
        scope: Optional[Union[Scope, ObjectID]] = None,
        context_group: Optional[ContextGroup] = None,
        **kwargs,
    ) -> List[Context]:
        """
        Retrieve Contexts.

        .. versionadded:: 3.12

        :param pk: (optional) retrieve a single primary key (object ID)
        :param context_type: (optional) filter on context_type (should be of `ContextType`)
        :param activities: (optional) filter on a list of Activities or Activity Id's
        :param scope: (optional) filter on a scope.
        :return: a list of Contexts
        :rtype: List[Context]
        """
        request_params = {
            "id": check_uuid(pk),
            "context_type": check_enum(context_type, ContextType, "context"),
            "activities": check_list_of_base(activities, Activity, "activities"),
            "scope": check_base(scope, Scope, "scope"),
            "context_group": check_enum(context_group, ContextGroup, "context_group"),
        }
        request_params.update(API_EXTRA_PARAMS["contexts"])

        if kwargs:
            request_params.update(**kwargs)

        return Context.list(client=self, **request_params)

    def create_form_model(self, *args, **kwargs) -> Form:
        """
        Create a single Form Model.

        See the `Form.create_model()` method for available arguments.

        :return: a created Form Model
        """
        return Form.create_model(client=self, *args, **kwargs)

    def instantiate_form(self, model, *args, **kwargs) -> Form:
        """
        Create a new Form instance based on a model.

        See the `Form.instantiate()` method for available arguments.

        :return: a created Form Instance
        """
        return Form.instantiate(self=model, *args, **kwargs)

    def form(self, *args, **kwargs) -> Form:
        """
        Retrieve a single Form, see `forms()` method for available arguments.

        .. versionadded:: 3.20

        :return: a single Contexts
        :rtype: Context
        """
        return self._retrieve_singular(self.forms, *args, **kwargs)  # noqa

    def forms(
        self,
        name: Optional[str] = None,
        pk: Optional[ObjectID] = None,
        category: Optional[FormCategory] = None,
        description: Optional[str] = None,
        scope: Optional[Union[Scope, ObjectID]] = None,
        context: Optional[List[Union[Context, ObjectID]]] = None,
        ref: Optional[str] = None,
        **kwargs,
    ) -> List[Form]:
        """
        Retrieve Forms.

        .. versionadded:: 3.20

        :param pk: (optional) retrieve a single primary key (object ID)
        :param name: (optional) name of the form to filter on
        :param category: (optional) category of the form to search for
        :param description: (optional) description of the form to filter on
        :param scope: (optional) the scope of the form to filter on
        :param context: (optional) the context of the form to filter on
        :param ref: (optional) the ref of the form to filter on
        :return: a list of Forms
        """
        request_params = {
            "name": check_text(name, "name"),
            "id": check_uuid(pk),
            "category": check_enum(category, FormCategory, "category"),
            "description": check_text(description, "description"),
            "scope": check_base(scope, Scope, "scope"),
            "context_id__in": check_list_of_base(context, Context, "context"),
            "ref": check_text(ref, "ref"),
        }
        if kwargs:
            request_params.update(**kwargs)

        return Form.list(client=self, **request_params)

    def _create_forms_bulk(
        self,
        forms: List[Dict],
        asynchronous: Optional[bool] = False,
        retrieve_instances: Optional[bool] = True,
        **kwargs,
    ) -> List:
        """
        Create multiple form instances simultaneously.

        :param forms: list of dicts, each specifying a form instance. Available fields per dict:
            :param name: (optional) name provided for the new instance as string otherwise use
            the name of the model
            :type name: basestring or None
            :param description: (optional) description provided for the new instance as string
            otherwise use the description of the model
            :type description: basestring or None
            :param model_id: model of the form which to add new instances, should follow the
            model tree in KE-chain
            :type model_id: UUID
            :param contexts: list of contexts
            :type properties: list
        :type forms: list
        :param asynchronous: If true, immediately returns without forms (default = False)
        :type asynchronous: bool
        :param retrieve_instances: If true, will retrieve the created Form Instances in a List
        :type retrieve_instances: bool
        :param kwargs:
        :return: list of Form instances or list of form UUIDs
        :rtype list
        """
        check_list_of_dicts(
            forms,
            "forms",
            [
                "form",
                "values",
            ],
        )
        for form in forms:
            form["form"] = check_base(form.get("form"), Form, "form")
            form["values"]["contexts"] = check_list_of_base(
                form.get("values").get("contexts"), Context, "contexts"
            )

        # prepare url query parameters
        query_params = kwargs
        query_params.update(API_EXTRA_PARAMS["forms"])
        query_params["async_mode"] = asynchronous
        bulk_action_input = {"bulk_action_input": forms}
        response = self._request(
            "POST",
            self._build_url("forms_bulk_create_instances"),
            params=query_params,
            json=bulk_action_input,
        )

        if (asynchronous and response.status_code != requests.codes.accepted) or (
            not asynchronous and response.status_code != requests.codes.created
        ):  # pragma: no cover
            raise APIError(
                f"Could not create Forms. ({response.status_code})", response=response
            )
        form_ids = [form.get("id") for form in response.json()["results"]]
        if retrieve_instances:
            instances_per_id = dict()
            for forms_ids_chunk in get_in_chunks(lst=form_ids, chunk_size=50):
                instances_per_id.update(
                    {
                        p.id: p for p in self.forms(id__in=",".join(forms_ids_chunk))
                    }  # `id__in` does not guarantee order
                )
            form_instances = [
                instances_per_id[pk] for pk in form_ids
            ]  # Ensures order of parts wrt request
            return form_instances
        return form_ids

    def _delete_forms_bulk(
        self,
        forms: List[Union[Form, str]],
        asynchronous: Optional[bool] = False,
        **kwargs,
    ) -> bool:
        """Delete multiple Forms simultaneously.

        :param parts: list of Form objects or UUIDs
        :type parts: List[Form] or List[UUID]
        :param asynchronous: If true, immediately returns (default = False)
        :type asynchronous: bool
        :param kwargs:
        :return: True if forms are deleted successfully
        :raises APIError: if the forms could not be deleted
        :raises IllegalArgumentError: if there were neither Forms nor UUIDs in the list of forms
        """
        check_type(asynchronous, bool, "asynchronous")

        list_forms = list()
        for form in forms:
            if isinstance(form, Form):
                list_forms.append(form.id)
            elif is_uuid(form):
                list_forms.append(form)
            else:
                raise IllegalArgumentError(f"{form} is not a Form nor an UUID")
        query_params = kwargs
        query_params.update(API_EXTRA_PARAMS["parts"])
        query_params["async_mode"] = asynchronous
        bulk_action_input = {"bulk_action_input": list_forms}
        response = self._request(
            "DELETE",
            self._build_url("forms_bulk_delete"),
            params=query_params,
            json=bulk_action_input,
        )
        # TODO - remove requests.codes.ok when async is implemented in the backend
        if (
            asynchronous
            and response.status_code not in (requests.codes.ok, requests.codes.accepted)
        ) or (
            not asynchronous
            and response.status_code not in (requests.codes.ok, requests.codes.accepted)
        ):  # pragma: no cover
            raise APIError(
                f"Could not delete Forms. ({response.status_code})", response=response
            )
        return True

    def workflow(
        self,
        name: Optional[str] = None,
        pk: Optional[ObjectID] = None,
        category: Optional[WorkflowCategory] = None,
        description: Optional[str] = None,
        scope: Optional[Union[Scope, ObjectID]] = None,
        ref: Optional[str] = None,
        **kwargs,
    ) -> Workflow:
        """
        Retrieve a single Workflow, see `workflows()` method for available arguments.

        .. versionadded:: 3.20

        :param pk: (optional) retrieve a single primary key (object ID)
        :param name: (optional) name of the workflow to filter on
        :param category: (optional) category of the workflow to search for
        :param description: (optional) description of the workflow to filter on
        :param scope: (optional) the scope of the workflow to filter on
        :param ref: (optional) the ref of the workflow to filter on
        :return: a single Workflows
        :rtype: Workflow
        """
        request_params = {
            "name": check_text(name, "name"),
            "id": check_uuid(pk),
            "category": check_enum(category, WorkflowCategory, "category"),
            "description": check_text(description, "description"),
            "scope": check_base(scope, Scope, "scope"),
            "ref": check_text(ref, "ref"),
        }

        if kwargs:
            request_params.update(**kwargs)
        return Workflow.get(
            client=self, **clean_empty_values(request_params, nones=False)
        )

    def workflows(
        self,
        name: Optional[str] = None,
        pk: Optional[ObjectID] = None,
        category: Optional[WorkflowCategory] = None,
        description: Optional[str] = None,
        scope: Optional[Union[Scope, ObjectID]] = None,
        ref: Optional[str] = None,
        **kwargs,
    ) -> List[Workflow]:
        """
        Retrieve Workflows.

        .. versionadded:: 3.20

        :param pk: (optional) retrieve a single primary key (object ID)
        :param name: (optional) name of the workflow to filter on
        :param category: (optional) category of the workflow to search for
        :param description: (optional) description of the workflow to filter on
        :param scope: (optional) the scope of the workflow to filter on
        :param ref: (optional) the ref of the workflow to filter on
        :return: a list of Workflows
        """
        request_params = {
            "name": check_text(name, "name"),
            "id": check_uuid(pk),
            "category": check_enum(category, WorkflowCategory, "category"),
            "description": check_text(description, "description"),
            "scope": check_base(scope, Scope, "scope"),
            "ref": check_text(ref, "ref"),
        }

        if kwargs:
            request_params.update(**kwargs)

        return Workflow.list(client=self, **request_params)

    def create_workflow(self, scope: ObjectID, **kwargs) -> Workflow:
        """Create a new Defined Workflow object in a scope.

        See `Workflow.create` for available parameters.

        :return: a Workflow object
        """
        return Workflow.create(client=self, scope=scope, **kwargs)

    def import_parts(
        self,
        file,
        model: Part,
        parent: Part,
        activity: Optional[Activity] = None,
        async_mode: Optional[bool] = True,
    ) -> None:
        """Import parts from an Excel file.

        :param file: the Excel file to be used
        :param model: model of the Part
        :param parent: Parent Part instance
        :param activity: Optional
        :param async_mode: (boolean) if the call should be made asynchronously
        :return:
        """
        if model.category != Category.MODEL:
            raise IllegalArgumentError(f"Part {model.name} should be of category MODEL")
        if parent.category != Category.INSTANCE:
            raise IllegalArgumentError(
                f"Part {parent.name} should be of category INSTANCE"
            )

        json = dict(
            model_id=model.id,
            parent_id=parent.id,
            activity_id=activity.id,
        )
        params = dict(async_mode=async_mode)
        if isinstance(file, str):
            with open(file, "rb") as fp:
                url = self._build_url("parts_import")
                response = self._request(
                    "POST", url, data=json, params=params, files={"attachment": fp}
                )
                if response.status_code not in (
                    requests.codes.accepted,
                    requests.codes.ok,
                ):
                    raise APIError(
                        f"Could not import parts {str(response)}: {response.content}"
                    )

    def create_stored_file(self, **kwargs) -> StoredFile:
        """Create a new Stored File object in a scope.

        See `StoredFile.create` for available parameters.

        :return: a StoredFile object
        """
        return StoredFile.create(client=self, **kwargs)

    def stored_file(
        self,
        name: Optional[str] = None,
        pk: Optional[ObjectID] = None,
        scope: Optional[Union[Scope, ObjectID]] = None,
        category: Optional[StoredFileCategory] = None,
        classification: Optional[StoredFileClassification] = None,
        description: Optional[str] = None,
        ref: Optional[str] = None,
        **kwargs,
    ) -> StoredFile:
        """
        Retrieve a single Stored File.

        .. versionadded:: 4.7.0

        :param pk: (optional) retrieve a single primary key (object ID)
        :param name: (optional) name of the stored file to filter on
        :param category: (optional) category of the stored file to search for
        :param classification: (optional) classification of the stored file to search for
        :param description: (optional) description of the stored file to filter on
        :param scope: (optional) the scope of the stored file to filter on
        :param ref: (optional) the ref of the stored file to filter on

        :return: a single StoredFiles
        :rtype: StoredFile
        """
        request_params = {
            "name": check_text(name, "name"),
            "id": check_uuid(pk),
            "category": check_enum(category, StoredFileCategory, "category"),
            "classification": check_enum(
                classification, StoredFileClassification, "classification"
            ),
            "description": check_text(description, "description"),
            "scope": check_base(scope, Scope, "scope"),
            "ref": check_text(ref, "ref"),
        }

        if kwargs:
            request_params.update(**kwargs)
        return StoredFile.get(
            client=self, **clean_empty_values(request_params, nones=False)
        )

    def stored_files(
        self,
        name: Optional[str] = None,
        pk: Optional[ObjectID] = None,
        scope: Optional[Union[Scope, ObjectID]] = None,
        category: Optional[StoredFileCategory] = None,
        classification: Optional[StoredFileClassification] = None,
        description: Optional[str] = None,
        ref: Optional[str] = None,
        **kwargs,
    ) -> List[StoredFile]:
        """
        Retrieve a single Stored File.

        .. versionadded:: 4.7.0

        :param pk: (optional) retrieve a single primary key (object ID)
        :param name: (optional) name of the stored file to filter on
        :param category: (optional) category of the stored file to search for
        :param classification: (optional) classification of the stored file to search for
        :param description: (optional) description of the stored file to filter on
        :param scope: (optional) the scope of the stored file to filter on
        :param ref: (optional) the ref of the stored file to filter on

        :return: a list of StoredFiles
        """
        request_params = {
            "name": check_text(name, "name"),
            "id": check_uuid(pk),
            "category": check_enum(category, StoredFileCategory, "category"),
            "classification": check_enum(
                classification, StoredFileClassification, "classification"
            ),
            "description": check_text(description, "description"),
            "scope": check_base(scope, Scope, "scope"),
            "ref": check_text(ref, "ref"),
        }

        if kwargs:
            request_params.update(**kwargs)
        return StoredFile.list(
            client=self, **clean_empty_values(request_params, nones=False)
        )
