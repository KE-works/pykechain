from typing import Any, AnyStr  # flake8: noqa

import requests
from six import text_type

from pykechain.exceptions import APIError
from pykechain.models.base import Base


class Property(Base):
    """A virtual object representing a KE-chain property."""

    def __init__(self, json, **kwargs):
        # type: (dict, **Any) -> None
        """Construct a Property from a json object."""
        super(Property, self).__init__(json, **kwargs)

        self._output = json.get('output')
        self._value = json.get('value')

    @property
    def output(self):
        """Return true if the property is configured as an output.

        :return: True if the property output is configured as output, otherwise false
        """
        return self._json_data.get('output', False)

    @property
    def value(self):
        # type: () -> Any
        """Retrieve the data value of a property.

        Setting this value will immediately update the property in KE-chain.
        """
        return self._value

    @value.setter
    def value(self, value):
        # type: (Any) -> None
        if self._put_value(value):
            self._value = value
            self._json_data['value'] = value

    @property
    def part(self):
        """Retrieve the part that holds this Property."""
        part_id = self._json_data['part']

        return self._client.part(pk=part_id, category=self._json_data['category'])

    def delete(self):
        """Delete this property.

        :return: None
        :raises: APIError if delete was not successful
        """
        r = self._client._request('DELETE', self._client._build_url('property', property_id=self.id))

        if r.status_code != requests.codes.no_content: # pragma: no cover
            raise APIError("Could not delete property: {} with id {}".format(self.name, self.id))

    def _put_value(self, value):
        url = self._client._build_url('property', property_id=self.id)

        r = self._client._request('PUT', url, json={'value': value})

        if r.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update property value")

        return r.json()['results'][0]['value']

    @classmethod
    def create(cls, json, **kwargs):
        # type: (dict, **Any) -> Property
        """Create a property based on the json data.

        This method will attach the right class to a property, enabling the use of type-specific methods.
        """
        property_type = json.get('property_type')

        if property_type == 'ATTACHMENT_VALUE':
            from .property_attachment import AttachmentProperty
            return AttachmentProperty(json, **kwargs)
        elif property_type == 'SINGLE_SELECT_VALUE':
            from .property_selectlist import SelectListProperty
            return SelectListProperty(json, **kwargs)
        elif property_type == 'REFERENCE_VALUE':
            from .property_reference import ReferenceProperty
            return ReferenceProperty(json, **kwargs)
        else:
            return Property(json, **kwargs)

    def edit(self, name=None, description=None, unit=None):
        # type: (AnyStr, AnyStr, AnyStr) -> None
        """
        Edit the details of a property (model).

        :param name: (optional) new name of the property to edit
        :param description: (optional) new description of the property
        :param unit: (optional) new unit of the property
        :return: None
        :raises: APIError

        Example
        -------
        >>> front_fork = project.part('Front Fork')
        >>> color_property = front_fork.property(name='Color')
        >>> color_property.edit(name='Shade', description='Could also be called tint, depending on mixture',
        >>> unit='RGB')

        """
        update_dict = {'id': self.id}
        if name:
            if not isinstance(name, (str, text_type)):
                raise TypeError("name should be provided as a string, was provided as '{}'".format(type(name)))
            update_dict.update({'name': name})
            self.name = name
        if description:
            if not isinstance(description, (str, text_type)):
                raise TypeError("description should be provided as a string, was provided as '{}'".
                                format(type(description)))
            update_dict.update({'description': description})
        if unit:
            if not isinstance(unit, (str, text_type)):
                raise TypeError("unit should be provided as a string, was provided as '{}'".
                                format(type(unit)))
            update_dict.update({'unit': unit})

        r = self._client._request('PUT', self._client._build_url('property', property_id=self.id), json=update_dict)

        if r.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Property ({})".format(r))

