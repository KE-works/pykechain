from typing import Any, List, Dict, Optional, Text, Union, Tuple, Iterable, TypeVar

import requests
from jsonschema import validate

from pykechain.enums import Category
from pykechain.exceptions import APIError, IllegalArgumentError
from pykechain.models import Base, BaseInScope
from pykechain.models.input_checks import check_text, check_type
from pykechain.models.representations.component import RepresentationsComponent
from pykechain.models.validators import PropertyValidator
from pykechain.models.validators.validator_schemas import options_json_schema
from pykechain.defaults import API_EXTRA_PARAMS

T = TypeVar("T")


class Property2(BaseInScope):
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

    _use_bulk_update = False
    _update_package = list()

    def __init__(self, json, **kwargs):
        """Construct a Property from a json object."""
        super().__init__(json, **kwargs)

        self.output = json.get('output')  # type: bool
        self.model_id = json.get('model_id')  # type: Optional[Text]
        self.part_id = json.get('part_id')
        self.ref = json.get('ref')
        self.type = json.get('property_type')
        self.category = json.get('category')
        self.description = json.get('description', None)
        self.unit = json.get('unit', None)
        self.order = json.get('order')

        # Create protected variables
        self._value = json.get('value')  # type: Any
        self._options = json.get('value_options', {})  # type: Dict
        self._part = None  # type: Optional['Part2']
        self._model = None  # type: Optional['Property2']
        self._validators = []  # type: List[PropertyValidator]
        self._validation_results = []  # type: List
        self._validation_reasons = []  # type: List

        self._representations_container = RepresentationsComponent(
            self,
            self._options.get('representations', {}),
            self._save_representations,
        )

        validate(self._options, options_json_schema)

        if self._options.get('validators'):
            self._parse_validators()

    def refresh(self, json: Optional[Dict] = None, url: Optional[Text] = None, extra_params: Optional = None) -> None:
        """Refresh the object in place."""
        super().refresh(json=json,
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

    @property
    def use_bulk_update(self):
        """Set or get the toggle to asynchronously update property values."""
        # set the class attribute to make this value a singleton
        return self.__class__._use_bulk_update

    @use_bulk_update.setter
    def use_bulk_update(self, value):
        assert isinstance(value, bool), "`use_bulk_update` must be set to a boolean, not {}".format(type(value))
        self.__class__._use_bulk_update = value

    @property
    def value(self) -> Any:
        """Retrieve the data value of a property.

        Setting this value will immediately update the property in KE-chain.

        :returns: the value
        """
        return self._value

    @value.setter
    def value(self, value: Any) -> None:
        value = self.serialize_value(value)
        if self.use_bulk_update:
            self._pend_value(value)
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

    def _pend_value(self, value):
        """Store the value to be send at a later point in time using `update_values`."""
        self.__class__._update_package.append(dict(
            id=self.id,
            value=value,
        ))
        self._value = value
        return self._value

    def _put_value(self, value):
        """Send the value to KE-chain."""
        url = self._client._build_url('property2', property_id=self.id)

        response = self._client._request('PUT', url, params=API_EXTRA_PARAMS['property2'], json={'value': value})

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Property {}".format(self), response=response)

        self.refresh(json=response.json()['results'][0])
        return self._value

    def serialize_value(self, value: [T]) -> T:
        """
        Serialize the value to be set on the property.

        :param value: non-serialized value
        :type value: Any
        :return: serialized value
        """
        return value.id if isinstance(value, Base) else value

    @property
    def part(self) -> 'Part2':
        """
        Retrieve the part that holds this Property.

        :returns: The :class:`Part` associated to this property
        :raises APIError: if the `Part` is not found
        """
        if self._part is None:
            self._part = self._client.part(pk=self.part_id, category=self.category)
        return self._part

    def model(self) -> 'AnyProperty':
        """
        Model object of the property if the property is an instance otherwise itself.

        Will cache the model object in order to not generate too many API calls. Otherwise will make an API call
        to the backend to retrieve its model object.

        :return: `Property` model object if the current `Property` is an instance.
        :rtype: :class:`pykechain.models.AnyProperty`
        """
        if self.category == Category.MODEL:
            return self
        elif self._model is None:
            self._model = self._client.property(pk=self.model_id, category=Category.MODEL)
        return self._model

    @property
    def validators(self):
        """Provide list of Validator objects.

        :returns: list of :class:`PropertyValidator` objects
        :rtype: list(PropertyValidator)
        """
        return self._validators

    @validators.setter
    def validators(self, validators: Iterable[PropertyValidator]) -> None:
        if self.category != Category.MODEL:
            raise IllegalArgumentError("To update the list of validators, it can only work on "
                                       "`Property` of category 'MODEL'")

        if not isinstance(validators, (tuple, list)) or not all(isinstance(v, PropertyValidator) for v in validators):
            raise IllegalArgumentError('Should be a list or tuple with PropertyValidator objects, '
                                       'got {}'.format(type(validators)))
        for validator in validators:
            validator.validate_json()

        # set the internal validators list
        self._validators = list(set(validators))

        # dump to _json options
        self._dump_validators()

        # update the options to KE-chain backend
        self.edit(options=self._options)

    def _parse_validators(self):
        """Parse the validator in the options to validators."""
        self._validators = []
        validators_json = self._options.get('validators')
        for validator_json in validators_json:
            self._validators.append(PropertyValidator.parse(json=validator_json))

    def _dump_validators(self):
        """Dump the validators as json inside the _options dictionary with the key `validators`."""
        validators_json = []
        for validator in self._validators:
            if isinstance(validator, PropertyValidator):
                validators_json.append(validator.as_json())
            else:
                raise APIError("validator is not a PropertyValidator: '{}'".format(validator))
        if self._options.get('validators', list()) == validators_json:
            # no change
            pass
        else:
            new_options = self._options.copy()  # make a copy
            new_options.update({'validators': validators_json})
            validate(new_options, options_json_schema)
            self._options = new_options

    @property
    def is_valid(self) -> Optional[bool]:
        """Determine if the value in the property is valid.

        If the value of the property is validated as 'valid', than returns a True, otherwise a False.
        When no validators are configured, returns a None. It checks against all configured validators
        and returns a single boolean outcome.

        :returns: True when the `value` is valid
        :rtype: bool or None
        """
        if not self._validators:
            return None
        else:
            self.validate(reason=False)
            if all([vr is None for vr in self._validation_results]):
                return None
            else:
                return all(self._validation_results)

    @property
    def is_invalid(self) -> Optional[bool]:
        """Determine if the value in the property is invalid.

        If the value of the property is validated as 'invalid', than returns a True, otherwise a False.
        When no validators are configured, returns a None. It checks against all configured validators
        and returns a single boolean outcome.

        :returns: True when the `value` is invalid
        :rtype: bool
        """
        return not self.is_valid if self.is_valid is not None else None

    def validate(self, reason: bool = True) -> List[Union[bool, Tuple]]:
        """Return the validation results and include an (optional) reason.

        If reason keyword is true, the validation is returned for each validation
        the [(<result: bool>, <reason:str>), ...]. If reason is False, only a single list of validation results
        for each configured validator is returned.

        :param reason: (optional) switch to indicate if the reason of the validation should be provided
        :type reason: bool
        :return: list of validation results [bool, bool, ...] or
                 a list of validation results, reasons [(bool, str), ...]
        :rtype: list(bool) or list((bool, str))
        :raises Exception: for incorrect validators or incompatible values
        """
        self._validation_results = [validator.is_valid(self._value) for validator in self._validators]
        self._validation_reasons = [validator.get_reason() for validator in self._validators]

        if reason:
            return list(zip(self._validation_results, self._validation_reasons))
        else:
            return self._validation_results

    @property
    def representations(self):
        """Get and set the property representations."""
        return self._representations_container.get_representations()

    @representations.setter
    def representations(self, value):
        if self.category != Category.MODEL:
            raise IllegalArgumentError("To update the list of representations, it can only work on a "
                                       "`Property` of category '{}'".format(Category.MODEL))

        self._representations_container.set_representations(value)

    def _save_representations(self, representation_options):
        self._options.update({'representations': representation_options})
        self.edit(options=self._options)

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

        from pykechain.models import property_type_to_class_map

        # Get specific Property subclass, defaulting to Property2 itself
        property_class = property_type_to_class_map.get(property_type, Property2)

        # Call constructor and return new object
        return property_class(json, **kwargs)

    def edit(
            self,
            name: Optional[Text] = None,
            description: Optional[Text] = None,
            unit: Optional[Text] = None,
            options: Optional[Dict] = None,
            **kwargs
    ) -> None:
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
        update_dict = {
            'id': self.id,
            'name': check_text(name, 'name') or self.name,
            'description': check_text(description, 'description') or self.description,
        }

        options = check_type(options, dict, 'options')
        if options:
            update_dict['value_options'] = options

        unit = check_text(unit, 'unit')
        if unit:
            update_dict['unit'] = unit

        if kwargs:  # pragma: no cover
            update_dict.update(kwargs)

        response = self._client._request('PUT',
                                         self._client._build_url('property2', property_id=self.id),
                                         params=API_EXTRA_PARAMS['property2'],
                                         json=update_dict)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Property {}".format(self), response=response)

        self.refresh(json=response.json()['results'][0])

    def delete(self) -> None:
        """Delete this property.

        :return: None
        :raises APIError: if delete was not successful
        """
        response = self._client._request('DELETE', self._client._build_url('property2', property_id=self.id))

        if response.status_code != requests.codes.no_content:  # pragma: no cover
            raise APIError("Could not delete Property {}".format(self), response=response)

    def copy(self, target_part: 'Part2', name: Optional[Text] = None) -> 'Property2':
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
        check_type(target_part, Part2, 'target_part')

        name = check_text(name, 'name') or self.name
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

    def move(self, target_part: 'Part2', name: Optional[Text] = None) -> 'Property2':
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
