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

    def refresh(self, json=None, url=None, extra_params=None):
        """Refresh the object in place.

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
