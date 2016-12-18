

class Base(object):

    def __init__(self, json):
        self._json_data = json

        self.id = json.get('id')
        self.name = json.get('name')
