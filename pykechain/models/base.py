

class Base(object):

    def __init__(self, json, client=None):
        self._json_data = json
        self._client = client

        self.id = json.get('id')
        self.name = json.get('name')
