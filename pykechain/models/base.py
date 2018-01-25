class Base(object):
    """Base model connecting retrieved data to a KE-chain client.

    :cvar basestring id: The UUID of the object (corresponds with the UUID in KE-chain).
    :cvar basestring name: The name of the object.
    """

    def __init__(self, json, client):
        """Construct a model from provided json data."""
        self._json_data = json
        self._client = client

        self.id = json.get('id', None)
        self.name = json.get('name', None)

    def __repr__(self):  # pragma: no cover
        return "<pyke {} '{}' id {}>".format(self.__class__.__name__, self.name, self.id[-8:])

    def __eq__(self, other):  # pragma: no cover
        if hasattr(self, 'id') and hasattr(other, 'id'):
            return self.id == other.id
        else:
            return self == other

    def refresh(self):
        # type: () -> None
        """Refresh the object in place."""
        src = self._client.reload(self)
        self.__dict__.update(src.__dict__)
