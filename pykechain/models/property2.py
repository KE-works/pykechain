from typing import Any, List, Dict, Optional, Text  # noqa: F401

import requests
from jsonschema import validate
from six import text_type, iteritems

from pykechain.enums import PropertyType, Category
from pykechain.exceptions import APIError, IllegalArgumentError
from pykechain.models.property import Property
from pykechain.models.representations.representation_base import BaseRepresentation
from pykechain.models.validators.validator_schemas import options_json_schema
from pykechain.defaults import API_EXTRA_PARAMS


class Property2(Property):
    """A virtual object representing a KE-chain property.

    .. versionadded: 3.0
       This is a `Property` to communicate with a KE-chain 3 backend.

    :cvar bulk_update: flag to postpone update of properties until manually requested
    :type bulk_update: bool
    :ivar type: The property type of the property. One of the types described in :class:`pykechain.enums.PropertyType`
    :type type: str
    :ivar category: The category of the property, either `Category.MODEL` of `Category.INSTANCE`
    :type category: str
    :ivar description: description of the property
    :type description: str or None
    :ivar unit: unit of measure of the property
    :type unit: str or None
    :ivar model: the id of the model (not the model object)
    :type model: str
    :ivar output: a boolean if the value is configured as an output (in an activity)
    :type output: bool
    :ivar scope_id: the id of the Scope (not the `Scope` object)
    :type scope_id: str
    :ivar part: The (parent) part in which this property is available
    :type part: :class:`Part2`
    :ivar value: the property value, can be set as well as property
    :type value: Any
    :ivar validators: the list of validators that are available in the property
    :type validators: List[PropertyValidator]
    :ivar is_valid: if the property conforms to the validators
    :type is_valid: bool
    :ivar is_invalid: if the property does not conform to the validator
    :type is_invalid: bool
    """

    use_bulk_update = False
    _update_package = list()

    def __init__(self, json, **kwargs):
        """Construct a Property from a json object."""
        super(Property2, self).__init__(json, **kwargs)

        self._output = json.get('output')
        self._value = json.get('value')
        self._options = json.get('value_options')
        self._part = None  # Part2 storage
        self._model = None  # Model object storage

        self.part_id = json.get('part_id')
        self.scope_id = json.get('scope_id')
        self.ref = json.get('ref')
        self.type = json.get('property_type')
        self.category = json.get('category')
        self.description = json.get('description', None)
        self.unit = json.get('unit', None)
        self.order = json.get('order')

        # set an empty internal validators variable
        self._validators = []  # type: List[Any]
        self._representations = []  # type: List[BaseRepresentation]

        if self._options:
            validate(self._options, options_json_schema)
            if self._options.get('validators'):
                self._parse_validators()
            if self._options.get('representations'):
                self._parse_representations()

    @property
    def value(self) -> Any:
        """Retrieve the data value of a property.

        Setting this value will immediately update the property in KE-chain.

        :returns: the value
        """
        return self._value

    @value.setter
    def value(self, value: Any) -> None:
        if self.use_bulk_update:
            self.__class__._update_package.append(dict(
                id=self.id,
                value=value,
            ))
            self._value = value
        else:
            self._put_value(value)

    @classmethod
    def update_values(cls, client: 'Client', use_bulk_update: bool = False) -> None:
        """
        Perform the bulk update of property values using the stored values in the `Property` class.

        :param client: Client object
        :type client: Client
        :param use_bulk_update: set the class attribute, defaults to False.
        :type use_bulk_update: bool
        :return: None
        """
        if cls.use_bulk_update:
            client.update_properties(properties=cls._update_package)
            cls._update_package = list()
        cls.use_bulk_update = use_bulk_update

    def _put_value(self, value):
        url = self._client._build_url('property2', property_id=self.id)

        response = self._client._request('PUT', url, params=API_EXTRA_PARAMS['property2'], json={'value': value})

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update property value: '{}'".format(response.content))

        self.refresh(json=response.json()['results'][0])
        return self._value

    @property
    def model_id(self):
        # type: () -> (type(None), Part2)  # noqa: F821
        """Model id of the Property.

        Returns None if the property is a model of its own. It will not return the model object, only the uuid.

        It will return None if the `model_id_name` field is not found in the response of the server.
        """
        if self.category == Category.MODEL:
            return None
        else:
            return self._json_data.get('model_id')

    @property
    def part(self):
        # type: () -> Part2  # noqa: F821
        """
        Retrieve the part that holds this Property.

        :returns: The :class:`Part` associated to this property
        :raises APIError: if the `Part` is not found
        """
        if self._part is None:
            self._part = self._client.part(pk=self.part_id, category=self.category)
        return self._part

    @property
    def representations(self):
        # type: () -> List[BaseRepresentation]
        """
        Provide list of representation objects.

        :return: list of Representations
        """
        return self._representations

    @representations.setter
    def representations(self, representations):
        # type: (List[BaseRepresentation]) -> None
        if self.category != Category.MODEL:
            raise IllegalArgumentError("To update the list of representations, it can only work on "
                                       "`Property` of category 'MODEL'")

        if not isinstance(representations, (tuple, list)):
            raise IllegalArgumentError('Should be a list or tuple with Representation objects, '
                                       'got {}'.format(type(representations)))
        for representation in representations:
            if not isinstance(representation, BaseRepresentation):
                raise IllegalArgumentError(
                    "Representation '{}' should be a Representation object".format(representation))
            representation.validate_json()

        # set the internal representation list
        self._representations = list(set(representations))

        # dump to _json options
        self._dump_representations()

        # update the options to KE-chain backend
        self.edit(options=self._options)

    def _parse_representations(self):
        """Parse the representations in the options to representations."""
        self._representations = []
        representations_json = self._options.get('representations')
        for representation_json in representations_json:
            self._representations.append(BaseRepresentation.parse(prop=self, json=representation_json))

    def _dump_representations(self):
        """Dump the representations as json inside the _options dictionary with the key `representations`."""
        if hasattr(self, '_representations'):
            representations_json = []
            for representation in self._representations:
                if isinstance(representation, BaseRepresentation):
                    representations_json.append(representation.as_json())
                else:
                    raise APIError("representation is not a BaseRepresentation: '{}'".format(representation))
            if self._options.get('representations', list()) == representations_json:
                # no change
                pass
            else:
                new_options = self._options.copy()  # make a copy
                new_options.update({'representations': representations_json})
                validate(new_options, options_json_schema)
                self._options = new_options

    @classmethod
    def create(cls, json: dict, **kwargs) -> 'AnyProperty':
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
        elif property_type == PropertyType.DATETIME_VALUE:
            from .property2_datetime import DatetimeProperty2
            return DatetimeProperty2(json, **kwargs)
        else:
            return Property2(json, **kwargs)

    def refresh(self, json=None, url=None, extra_params=None):
        # type: (Optional[Dict], Optional[Text], Optional) -> ()
        """Refresh the object in place."""
        super(Property2, self).refresh(json=json,
                                       url=self._client._build_url('property2', property_id=self.id),
                                       extra_params=API_EXTRA_PARAMS['property2'])

    def has_value(self) -> bool:
        """Predicate to indicate if the property has a value set.

        This predicate determines if the property has a value set. It will not make a call to KE-chain API (in case
        of reference properties). So it is a tiny fraction 'cheaper' in terms of processing time than checking the
        `Property.value` itself.

        It will return True if the property_type is a Boolean and set to a value of False.

        :returns: True if the property has a value set, otherwise (also when value is None) returns False
        :rtype: Bool
        """
        if isinstance(self._value, (float, int, bool)):
            return True  # to prevent "bool(0.00) = False" or "False = False"
        else:
            return bool(self._value)

    def edit(self, name=None, description=None, unit=None, options=None, **kwargs):
        # type: (Optional[Text], Optional[Text], Optional[Text], Optional[Dict], **Any) -> ()
        """Edit the details of a property (model).

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
        if name is not None:
            if not isinstance(name, (str, text_type)):
                raise IllegalArgumentError(
                    "name should be provided as a string, was provided as '{}'".format(type(name)))
            update_dict.update({'name': name})
            self.name = name
        if description is not None:
            if not isinstance(description, (str, text_type)):
                raise IllegalArgumentError("description should be provided as a string, was provided as '{}'".
                                           format(type(description)))
            update_dict.update({'description': description})
        if unit is not None:
            if not isinstance(unit, (str, text_type)):
                raise IllegalArgumentError("unit should be provided as a string, was provided as '{}'".
                                           format(type(unit)))
            update_dict.update({'unit': unit})
        if options is not None:
            if not isinstance(options, dict):
                raise IllegalArgumentError("options should be provided as a dict, was provided as '{}'".
                                           format(type(options)))
            update_dict.update({'value_options': options})
        if kwargs is not None:
            # process the other kwargs in py27 style.
            for key, value in iteritems(kwargs):
                update_dict[key] = value

        response = self._client._request('PUT',
                                         self._client._build_url('property2', property_id=self.id),
                                         params=API_EXTRA_PARAMS['property2'],
                                         json=update_dict)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Property ({})".format(response))

        self.refresh(json=response.json()['results'][0])

    def delete(self):
        # type: () -> ()
        """Delete this property.

        :return: None
        :raises APIError: if delete was not successful
        """
        response = self._client._request('DELETE', self._client._build_url('property2', property_id=self.id))

        if response.status_code != requests.codes.no_content:  # pragma: no cover
            raise APIError("Could not delete property: {} with id {}".format(self.name, self.id))

    def copy(self, target_part, name=None):
        # type: (Part2, Optional[Text]) -> Property2
        """Copy a property model or instance.

        :param target_part: `Part` object under which the desired `Property` is copied
        :type target_part: :class:`Part`
        :param name: how the copied `Property` should be called
        :type name: basestring
        :return: copied :class:`Property` model.
        :raises IllegalArgumentError: if property and target_part have different `Category`

        Example
        -------
        >>> property_to_copy = client.property(name='Diameter')
        >>> bike = client.model('Bike')
        >>> property_to_copy.copy(target_part=bike, name='Bike diameter?')

        """
        from pykechain.models import Part2
        if not isinstance(target_part, Part2):
            raise IllegalArgumentError("`target_part` needs to be a part, got '{}'".format(type(target_part)))
        if not name:
            name = self.name
        if self.category == Category.MODEL and target_part.category == Category.MODEL:
            # Cannot move a `Property` model under a `Part` instance or vice versa
            copied_property_model = target_part.add_property(name=name,
                                                             property_type=self.type,
                                                             description=self.description,
                                                             unit=self.unit,
                                                             default_value=self.value,
                                                             options=self._options
                                                             )
            return copied_property_model
        elif self.category == Category.INSTANCE and target_part.category == Category.INSTANCE:
            target_model = target_part.model()
            self_model = self.model()
            target_model.add_property(name=name,
                                      property_type=self_model.type,
                                      description=self_model.description,
                                      unit=self_model.unit,
                                      default_value=self_model.value,
                                      options=self_model._options
                                      )
            target_part.refresh()
            copied_property_instance = target_part.property(name=name)
            copied_property_instance.value = self.value
            return copied_property_instance
        else:
            raise IllegalArgumentError('property "{}" and target part "{}" must have the same category'.
                                       format(self.name, target_part.name))

    def move(self, target_part, name=None):
        # type: (Part2, Optional[Text]) -> Property2  # noqa: F821
        """Move a property model or instance.

        :param target_part: `Part` object under which the desired `Property` is moved
        :type target_part: :class:`Part`
        :param name: how the moved `Property` should be called
        :type name: basestring
        :return: copied :class:`Property` model.
        :raises IllegalArgumentError: if property and target_part have different `Category`

        Example
        -------
        >>> property_to_move = client.property(name='Diameter')
        >>> bike = client.model('Bike')
        >>> property_to_move.move(target_part=bike, name='Bike diameter?')

        """
        moved_property = self.copy(target_part=target_part, name=name)

        if self.category == Category.MODEL:
            self.delete()
        else:
            self.model().delete()
        return moved_property
