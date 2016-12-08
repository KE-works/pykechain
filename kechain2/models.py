import requests

from kechain2.utils import find


class Part(object):

    def __init__(self, json):
        self._json_data = json

        self.id = json.get('id')
        self.name = json.get('name')

        self.properties = [Property(p) for p in json['properties']]

    def property(self, name):
        found = find(self.properties, lambda p: name == p.name)

        assert found, "Could not find property with name {}".format(name)

        return found


class Property(object):

    def __init__(self, json):
        self._json_data = json

        self.id = json.get('id')
        self.name = json.get('name')

        self._value = json.get('value')

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value != self._value:
            self._put_value(value)
            self._value = value

    def _put_value(self, value):
        from kechain2.api import api_url, HEADERS

        r = requests.put(api_url('property', property_id=self.id), headers=HEADERS, json={
            'value': value
        })

        assert r.status_code == 200, "Could not update property value"
