import requests
from jsonschema import validate
from six import text_type, iteritems

from pykechain.enums import PropertyType, Category
from pykechain.exceptions import APIError, IllegalArgumentError
from pykechain.models.property import Property
from pykechain.models.validators.validator_schemas import options_json_schema


class Property2(Property):

    def __init__(self, json, **kwargs):
        super(Property2, self).__init__(json, **kwargs)
        self._options = json.get('value_options', None)

        if self._options:
            validate(self._options, options_json_schema)
            if self._options.get('validators'):
                self.__parse_validators()

    def _put_value(self, value):
        url = self._client._build_url('property2', property_id=self.id)

        from pykechain.client import API_EXTRA_PARAMS
        response = self._client._request('PUT', url, params=API_EXTRA_PARAMS['property2'], json={'value': value})

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update property value: '{}'".format(response.content))

        return response.json()['results'][0]['value']

    @property
    def model_id(self):
        """The model id of the Property.

        Returns None if the property is a model of its own. It will not return the model object, only the uuid.

        It will return None if the `model_id_name` field is not found in the response of the server.
        """
        if self.category == Category.MODEL:
            return None
        else:
            return self._json_data.get('model_id')

    @property
    def part(self):
        """Retrieve the part that holds this Property.

        :returns: The :class:`Part` associated to this property
        :raises APIError: if the `Part` is not found
        """
        part_id = self._json_data['part_id']

        return self._client.part(pk=part_id, category=self._json_data['category'])

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

    def edit(self, name=None, description=None, unit=None, options=None, **kwargs):
        """
        Edit the details of a property (model).

        :param name: (optional) new name of the property to edit
        :type name: basestring or None
        :param description: (optional) new description of the property
        :type description: basestring or None
        :param unit: (optional) new unit of the property
        :type unit: basestring or None
        :param options: (options) new options of the property
        :type options: dict
        :param kwargs: (optional) additional kwargs to be edited
        :type kwargs: dict or None
        :return: None
        :raises APIError: When unable to edit the property
        :raises IllegalArgumentError: when the type of the input is provided incorrect.

        Examples
        --------
        >>> front_fork = project.part('Front Fork')
        >>> color_property = front_fork.property(name='Color')
        >>> color_property.edit(name='Shade', description='Could also be called tint, depending on mixture',
        >>> unit='RGB')

        --------
        >>> wheel_property_reference = self.project.model('Bike').property('Reference wheel')
        >>> wheel_model = self.project.model('Wheel')
        >>> diameter_property = wheel_model.property('Diameter')
        >>> spokes_property = wheel_model.property('Spokes')
        >>> prefilters = {'property_value': diameter_property.id + ":{}:lte".format(15)}
        >>> propmodels_excl = [spokes_property.id]
        >>> options = dict()
        >>> options['prefilters'] = prefilters
        >>> options['propmodels_excl'] = propmodels_excl
        >>> wheel_property_reference.edit(options=options)

        """
        update_dict = {'id': self.id}
        if name:
            if not isinstance(name, (str, text_type)):
                raise IllegalArgumentError(
                    "name should be provided as a string, was provided as '{}'".format(type(name)))
            update_dict.update({'name': name})
            self.name = name
        if description:
            if not isinstance(description, (str, text_type)):
                raise IllegalArgumentError("description should be provided as a string, was provided as '{}'".
                                           format(type(description)))
            update_dict.update({'description': description})
        if unit:
            if not isinstance(unit, (str, text_type)):
                raise IllegalArgumentError("unit should be provided as a string, was provided as '{}'".
                                           format(type(unit)))
            update_dict.update({'unit': unit})
        if options:
            if not isinstance(options, dict):
                raise IllegalArgumentError("options should be provided as a dict, was provided as '{}'".
                                           format(type(options)))
            update_dict.update({'options': options})
        if kwargs:
            # process the other kwargs in py27 style.
            for key, value in iteritems(kwargs):
                update_dict[key] = value

        from pykechain.client import API_EXTRA_PARAMS
        response = self._client._request('PUT',
                                  self._client._build_url('property2', property_id=self.id),
                                  params=API_EXTRA_PARAMS['property2'],
                                  json=update_dict)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Property ({})".format(response))

        self.__init__(json=response.json()['results'][0], client=self._client)

    def delete(self):
        # type () -> ()
        """Delete this property.

        :return: None
        :raises APIError: if delete was not successful
        """
        response = self._client._request('DELETE', self._client._build_url('property2', property_id=self.id))

        if response.status_code != requests.codes.no_content:  # pragma: no cover
            raise APIError("Could not delete property: {} with id {}".format(self.name, self.id))
