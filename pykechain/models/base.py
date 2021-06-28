from typing import Dict, Optional, Text

from pykechain.utils import parse_datetime


class Base(object):
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

    def __init__(self, json: Dict, client: 'Client'):
        """Construct a model from provided json data."""
        self._json_data = json
        self._client: 'Client' = client

        self.id = json.get('id', None)
        self.name = json.get('name', None)
        self.created_at = parse_datetime(json.get('created_at'))
        self.updated_at = parse_datetime(json.get('updated_at'))

    def __repr__(self):  # pragma: no cover
        return "<pyke {} '{}' id {}>".format(self.__class__.__name__, self.name, self.id[-8:])

    def __eq__(self, other):  # pragma: no cover
        if hasattr(self, 'id') and hasattr(other, 'id'):
            return self.id == other.id
        else:
            return super().__eq__(other)

    def __hash__(self):
        return hash(self.id)

    def refresh(self, json: Optional[Dict] = None, url: Optional[Text] = None, extra_params: Optional[Dict] = None):
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


class BaseInScope(Base):
    """
    Base model for KE-chain objects coupled to a scope.

    :ivar scope_id: UUID of the Scope
    :type scope_id: str
    """

    def __init__(self, json, *args, **kwargs):
        """Append the scope ID to the attributes of the base object."""
        super().__init__(json, *args, **kwargs)

        self.scope_id = json.get('scope_id', json.get('scope', None))
        self._scope: Optional['Scope'] = None

    @property
    def scope(self):
        """
        Scope this object belongs to.

        This property will return a `Scope` object. It will make an additional call to the KE-chain API.

        :return: the scope
        :type: :class:`pykechain.models.Scope`
        :raises NotFoundError: if the scope could not be found
        """
        if not self._scope:
            self._scope = self._client.scope(pk=self.scope_id, status=None)
        return self._scope
