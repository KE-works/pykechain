from pykechain.exceptions import APIError
from pykechain.models import Base


class Property(Base):
    """A virtual object representing a KE-chain property."""

    def __init__(self, json, **kwargs):
        """Construct a Property from a json object."""
        super(Property, self).__init__(json, **kwargs)

        self.output = json.get('output')

        self._value = json.get('value')

    @property
    def value(self):
        """Data value of a property.

        Setting this value will immediately update the property in KE-chain.
        """
        return self._value

    @value.setter
    def value(self, value):
        if value != self._value:
            self._put_value(value)
            self._value = value

    @property
    def part(self):
        """Retrieve the part that holds this Property."""
        part_id = self._json_data['part']

        return self._client.part(pk=part_id)

    def delete(self):
        """Delete this property.

        :return: None
        :raises: APIError if delete was not successful
        """
        r = self._client._request('DELETE', self._client._build_url('property', property_id=self.id))

        if r.status_code != 204:
            raise APIError("Could not delete property: {} with id {}".format(self.name, self.id))

    def _put_value(self, value):
        url = self._client._build_url('property', property_id=self.id)

        r = self._client._request('PUT', url, json={'value': value})

        if r.status_code != 200:  # pragma: no cover
            raise APIError("Could not update property value")

    @classmethod
    def create(cls, json, **kwargs):
        """Create a property based on the json data.

        This method will attach the right class to a property, enabling the use of type-specific methods.
        """
        if json.get('property_type') == 'ATTACHMENT_VALUE':
            from .property_attachment import AttachmentProperty
            return AttachmentProperty(json, **kwargs)
        elif json.get('property_type') == 'SINGLE_SELECT_VALUE':
            from .property_selectlist import SelectListProperty
            return SelectListProperty(json, **kwargs)
        else:
            return Property(json, **kwargs)
