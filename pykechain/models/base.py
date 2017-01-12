

class Base(object):
    """Base model connecting retrieved data to a KE-chain client."""

    def __init__(self, json, client):
        """Construct a model from provided json data."""
        self._json_data = json
        self._client = client

        self.id = json.get('id')
        self.name = json.get('name')
