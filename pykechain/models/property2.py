import requests

from pykechain.enums import PropertyType, Category
from pykechain.exceptions import APIError
from pykechain.models.property import Property


class Property2(Property):
    pass

    def _put_value(self, value):
        url = self._client._build_url('property2', property_id=self.id)

        r = self._client._request('PUT', url, json={'value': value})

        if r.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update property value")

        return r.json()['results'][0]['value']

    @property
    def model_id(self):
        """The model id of the property.

        Returns None if the property is a model of its own. It will not return the model object.
        """
        if self.category == Category.MODEL:
            return None
        else:
            return self._json_data.get('model_id')

    @classmethod
    def create(cls, json, **kwargs):
        # type: (dict, **Any) -> Property
        """Create a property based on the json data.

        This method will attach the right class to a property, enabling the use of type-specific methods.

        It does not create a property object in KE-chain. But a pseudo :class:`Property` object.

        :param json: the json from which the :class:`Property` object to create
        :type json: dict
        :return: a :class:`Property` object
        """
        property_type = json.get('property_type')

        # changed for PIM2
        if property_type == PropertyType.ATTACHMENT_VALUE:
            from .property2_attachment import AttachmentProperty2
            return AttachmentProperty2(json, **kwargs)
        elif property_type == PropertyType.SINGLE_SELECT_VALUE:
            from .property2_selectlist import SelectListProperty2
            return SelectListProperty2(json, **kwargs)
        elif property_type == PropertyType.REFERENCES_VALUE:
            from .property2_multi_reference import MultiReferenceProperty2
            return MultiReferenceProperty2(json, **kwargs)
        else:
            return Property2(json, **kwargs)
