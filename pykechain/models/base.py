import warnings
from typing import Dict, List, Optional

import requests

from pykechain.defaults import API_EXTRA_PARAMS
from pykechain.exceptions import NotFoundError
from pykechain.models.input_checks import check_uuid, check_client
from pykechain.typing import ObjectID
from pykechain.utils import parse_datetime


class TooManyArgumentsWarning(UserWarning):
    """Warn a developer that too many arguments are used in the method call."""

    pass


class Base:
    """Base model connecting retrieved data to a KE-chain client.

    :ivar id: The UUID of the object (corresponds with the UUID in KE-chain).
    :type id: str
    :ivar name: The name of the object.
    :type name: basestring
    :ivar created_at: the datetime when the object was created if available (otherwise None)
    :type created_at: datetime or None
    :ivar updated_at: the datetime when the object was last updated if available (otherwise None)
    :type updated_at: datetime or None
    """

    def __init__(self, json: Dict, client: "Client"):
        """Construct a model from provided json data."""
        self._json_data = json
        self._client: "Client" = check_client(client)

        self.id = json.get("id")
        self.name = json.get("name")
        self.ref = json.get("ref")
        self.created_at = parse_datetime(json.get("created_at"))
        self.updated_at = parse_datetime(json.get("updated_at"))

    def __repr__(self):  # pragma: no cover
        return f"<pyke {self.__class__.__name__} '{self.name}' id {self.id[-8:]}>"

    def __eq__(self, other):  # pragma: no cover
        if hasattr(self, "id") and hasattr(other, "id"):
            return self.id == other.id
        else:
            return super().__eq__(other)

    def __hash__(self):
        return hash(self.id)

    def refresh(
        self,
        json: Optional[Dict] = None,
        url: Optional[str] = None,
        extra_params: Optional[Dict] = None,
    ):
        """Refresh the object in place.

        Can be called on the object without any arguments and should refresh the object inplace. If you want to
        use it in an advance way, you may call it with a json response from the server or provide the url to
        refetch the object from the server if the url cant be determined from the object itself.

        It is using the `Client.reload()` function to re-retrieve the object in a backend API call.

        :param json: (optional) json dictionary from a response from the server, will re-init object
        :type json: None or dict
        :param url: (optional) url to retrieve the object again, typically an identity url api/<service>/id
        :type url: None or basestring
        :param extra_params: (optional) additional paramenters (query params) for the request eg dict(fields='__all__')
        :type extra_params: None or dict
        """
        if json and isinstance(json, dict):
            self.__init__(json=json, client=self._client)
        else:
            src = self._client.reload(self, url=url, extra_params=extra_params)
            self.__dict__.update(src.__dict__)


class CrudActionsMixin:
    """
    Mixin that implements a list and get on the model.

    :cvar url_list_name: name of the list url in the defaults to contruct the api url
    :cvar url_detail_name: name of the detail url in the defaults to contruct the api url
    :cvar url_pk_name: name of the `<object>_id` as defined in the `API_PATH` in defaults
        for the detail url lookup on id.
    """

    url_list_name: str = None
    url_detail_name: str = None
    url_pk_name: str = None

    @classmethod
    def list(cls, client: "Client", **kwargs) -> List["self"]:
        """Retrieve a list of objects through the client."""
        if not cls.url_list_name:
            raise NotImplementedError(
                "This object type does not implement the list and get function on the object "
                "itself. It might be implemented in the Client object. \n"
                "[Pykechain Devs: If it is desired to implement the list/get functions "
                "on the object, the `cls.url_list_name` should match a uri string in the "
                "`defaults` for the `API_EXTRA_PARAMS` and the `API_PATH`.]"
            )

        kwargs.update(API_EXTRA_PARAMS[cls.url_list_name])
        response = client._request(
            "GET", client._build_url(cls.url_list_name), params=kwargs
        )

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError(f"Could not retrieve {cls.__name__}", response=response)

        return [cls(json=j, client=client) for j in response.json()["results"]]

    @classmethod
    def get(cls, client: "Client", **kwargs) -> "self":
        """Retrieve a single object using the client."""
        pk = None
        if "pk" in kwargs:
            pk = check_uuid(kwargs.pop("pk"))
        elif "id" in kwargs:
            # for accidental use of 'id' on the obj retrieving we have this smart
            # popper from the kwargs to ensure that the intention is still correct
            # it will result in a single obj retrieve.
            pk = check_uuid(kwargs.pop("id"))

        if pk:
            if not cls.url_detail_name:
                raise NotImplementedError(
                    "This object type does not implement the list and get function on the object "
                    "itself. It might be implemented in the Client object. \n"
                    "[Pykechain Devs: If it is desired to implement the list/get functions "
                    "on the object, the `cls.url_detail_name` should match a uri string in the "
                    "`defaults` for the `API_EXTRA_PARAMS` and the `API_PATH`.]"
                )
            # if more kwargs are provided, warn the developer that these will be ignored
            # and that the dev should alter the call to provide the `pk` only
            if kwargs:
                warnings.warn(
                    f"Too many arguments are passed to the method. Only the `pk` (or `id`) "
                    f"argument is used. The other arguments are not passed to the API and "
                    f"have no effect. Please alter the call to this method to reduce the "
                    f"number of arguments or use the '`list()` of <object>s' equivalent. "
                    f"Eg. if you want to filter on `pk` AND `category` you can use the "
                    f"list function. Got: {kwargs}",
                    UserWarning,
                )

            field_name_in_api_path = cls.url_pk_name or f"{cls.__name__.lower()}_id"
            url = client._build_url(cls.url_detail_name, **{field_name_in_api_path: pk})

            request_params = {}
            if cls.url_detail_name in API_EXTRA_PARAMS:
                request_params = API_EXTRA_PARAMS.get(cls.url_detail_name)
            elif cls.url_list_name in API_EXTRA_PARAMS:
                request_params = API_EXTRA_PARAMS.get(cls.url_list_name)

            response = client._request("GET", url, params=request_params)
            if response.status_code != requests.codes.ok:  # pragma: no cover
                raise NotFoundError("Could not retrieve object", response=response)
            return cls(response.json()["results"][0], client=client)

        # otherwise do the normal singular retrieve
        return client._retrieve_singular(cls.list, client=client, **kwargs)

    def delete(self) -> None:
        """
        Delete the object.

        After successful deletion on the server it will set the id to None to give feedback to the
        user that there is no relation between the object in memery and an object in KE-chain.
        """
        field_name_in_api_path = self.url_pk_name or f"{self.__name__.lower()}_id"
        url = self._client._build_url(
            self.url_detail_name, **{field_name_in_api_path: self.id}
        )

        response = self._client._request("DELETE", url)
        if response.status_code != requests.codes.no_content:
            raise NotFoundError("Could not delete object", response=response)
        # reset the id to None to feedback that the object is deleted in KE-chain
        self.id = None
        return None


class BaseInScope(Base):
    """
    Base model for KE-chain objects coupled to a scope.

    :ivar scope_id: UUID of the Scope
    :type scope_id: str
    """

    def __init__(self, json, *args, **kwargs):
        """Append the scope ID to the attributes of the base object."""
        super().__init__(json, *args, **kwargs)

        self.scope_id: Optional[ObjectID] = json.get(
            "scope_id", json.get("scope", None)
        )
        self._scope: Optional["Scope"] = None

    @property
    def scope(self):
        """
        Scope this object belongs to.

        This property will return a `Scope` object. It will make an additional call to the KE-chain API.

        :return: the scope
        :type: :class:`pykechain.models.Scope`
        :raises NotFoundError: if the scope could not be found
        """
        if not self._scope and self.scope_id:
            self._scope = self._client.scope(pk=self.scope_id, status=None)
        return self._scope


class NameDescriptionTranslationMixin:
    """Mixin that includes translations of the name and description of an object."""

    pass
