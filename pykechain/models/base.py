

class Base(object):

    def __init__(self, json, client=None):
        self._json_data = json
        self._client = client

        # If a client is not given, use default
        if not client:
            from pykechain.api import client
            self._client = client

        self.id = json.get('id')
        self.name = json.get('name')
