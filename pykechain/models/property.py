from pykechain.exceptions import APIError
from pykechain.models import Base


class Property(Base):
    def __init__(self, json, **kwargs):
        super(Property, self).__init__(json, **kwargs)

        self.output = json.get('output')

        self._value = json.get('value')

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value != self._value:
            self._put_value(value)
            self._value = value

    @property
    def part(self):
        part_id = self._json_data['part']

        return self._client.part(pk=part_id)

    def _put_value(self, value):
        url = self._client._build_url('property', property_id=self.id)

        r = self._client._request('PUT', url, json={'value': value})

        if r.status_code != 200:
            raise APIError("Could not update property value")

    @classmethod
    def create(cls, json, **kwargs):
        if json.get('property_type') == 'ATTACHMENT_VALUE':
            from pykechain.models import AttachmentProperty
            return AttachmentProperty(json, **kwargs)
        else:
            return Property(json, **kwargs)
