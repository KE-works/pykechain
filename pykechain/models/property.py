from typing import Any, Union, List  # noqa: F401

import requests
from jsonschema import validate
from six import text_type, iteritems

from pykechain.enums import PropertyType, Category
from pykechain.exceptions import APIError, IllegalArgumentError
from pykechain.models.base import BaseInScope
from pykechain.models.validators.validator_schemas import options_json_schema
from pykechain.models.validators.validators_base import PropertyValidator


class Property(BaseInScope):  # pragma: no cover
    """A virtual object representing a KE-chain property.

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
    :type part: :class:`Part`
    :ivar value: the property value, can be set as well as property
    :type value: Any
    :ivar validators: the list of validators that are available in the property
    :type validators: list(PropertyValidator)
    :ivar is_valid: if the property conforms to the validators
    :type is_valid: bool
    :ivar is_invalid: if the property does not conform to the validator
    :type is_invalid: bool
    """

    def __init__(self, json, **kwargs):
        # type: (dict, **Any) -> None
        """Construct a Property from a json object."""
        super(Property, self).__init__(json, **kwargs)

        self._output = json.get('output', None)
        self._value = json.get('value', None)
        self._options = json.get('options', None)
        self._model = None  # Model object storage
        self.type = json.get('property_type', None)
        self.category = json.get('category')
        self.description = json.get('description', None)
        self.unit = json.get('unit', None)
        self.order = json.get('order', None)

        # set an empty internal validators variable
        self._validators = []  # type: List[Any]

        if self._options:
            validate(self._options, options_json_schema)
            if self._options.get('validators'):
                self._parse_validators()

    @property
    def output(self):
        """Return true if the property is configured as an output.

        :return: True if the property output is configured as output, otherwise false
        :rtype: bool
        """
        return self._json_data.get('output', False)

    @property
    def value(self):
        # type: () -> Any
        """Retrieve the data value of a property.

        Setting this value will immediately update the property in KE-chain.

        :returns: the value
        """
        return self._value

    @value.setter
    def value(self, value):
        # type: (Any) -> None
        self._put_value(value)

    @property
    def validators(self):
        """Provide list of Validator objects.

        :returns: list of :class:`PropertyValidator` objects
        :rtype: list(PropertyValidator)
        """
        return self._validators

    @validators.setter
    def validators(self, validators):
        # type: (Union[list, tuple]) -> None
        if self.category != Category.MODEL:
            raise IllegalArgumentError("To update the list of validators, it can only work on "
                                       "`Property` of category 'MODEL'")

        if not isinstance(validators, (tuple, list)):
            raise IllegalArgumentError('Should be a list or tuple with PropertyValidator objects, '
                                       'got {}'.format(type(validators)))
        for validator in validators:
            if not isinstance(validator, PropertyValidator):
                raise IllegalArgumentError("Validator '{}' should be a PropertyValidator object".format(validator))
            validator.validate_json()

        # set the internal validators list
        self._validators = list(set(validators))

        # dump to _json options
        self._dump_validators()

        # update the options to KE-chain backend
        self.edit(options=self._options)

    @property
    def part(self):
        """Retrieve the part that holds this Property.

        :returns: The :class:`Part` associated to this property
        :raises APIError: if the `Part` is not found
        """
        part_id = self._json_data['part']

        return self._client.part(pk=part_id, category=self._json_data['category'])

    @property
    def model_id(self):
        """Model id of the property.

        Returns None if the property is a model of its own. It will not return the model.
        """
        if self.category == Category.MODEL:
            return None
        else:
            return self._json_data.get('model')

    def model(self):
        """
        Model object of the property if the property is an instance otherwise itself.

        Will cache the model object in order to not generate too many API calls. Otherwise will make an API call
        to the backend to retrieve its model object.

        :return: `Property` model object if the current `Property` is an instance.
        :rtype: :class:`pykechain.models.Property`
        """
        if self.category == Category.MODEL:
            return self
        elif self._model is None:
            self._model = self._client.property(pk=self.model_id, category=Category.MODEL)
        return self._model

    def delete(self):
        # type () -> ()
        """Delete this property.

        :return: None
        :raises APIError: if delete was not successful
        """
        response = self._client._request('DELETE', self._client._build_url('property', property_id=self.id))

        if response.status_code != requests.codes.no_content:  # pragma: no cover
            raise APIError("Could not delete property: {} with id {}".format(self.name, self.id))

    def _put_value(self, value):
        url = self._client._build_url('property', property_id=self.id)

        response = self._client._request('PUT', url, json={'value': value})

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update property value")

        self.refresh(url=url)  # update itself by requerying the url to retrieve all the information.
        return self.value

    def has_value(self):
        # type: () -> bool
        """Predicate to indicate if the property has a value set.

        This predicate determines if the property has a value set. It will not make a call to KE-chain API (in case
        of reference properties). So it is a tiny fraction 'cheaper' in terms of processing time than checking the
        `Property.value` itself.

        It will return True if the property_type is a Boolean and set to a value of False.

        :returns: True if the property has a value set, otherwise (also when value is None) returns False
        :rtype: Bool
        """
        return self._value is not None

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

        if property_type == PropertyType.ATTACHMENT_VALUE:
            from .property_attachment import AttachmentProperty
            return AttachmentProperty(json, **kwargs)
        elif property_type == PropertyType.SINGLE_SELECT_VALUE:
            from .property_selectlist import SelectListProperty
            return SelectListProperty(json, **kwargs)
        elif property_type == PropertyType.REFERENCE_VALUE:
            from .property_reference import ReferenceProperty
            return ReferenceProperty(json, **kwargs)
        elif property_type == PropertyType.REFERENCES_VALUE:
            from .property_multi_reference import MultiReferenceProperty
            return MultiReferenceProperty(json, **kwargs)
        elif property_type == PropertyType.DATETIME_VALUE:
            from .property_datetime import DatetimeProperty
            return DatetimeProperty(json, **kwargs)
        else:
            return Property(json, **kwargs)

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
            update_dict.update({'options': options})
        if kwargs is not None:
            # process the other kwargs in py27 style.
            for key, value in iteritems(kwargs):
                update_dict[key] = value

        response = self._client._request('PUT', self._client._build_url('property', property_id=self.id),
                                         json=update_dict)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Property ({})".format(response))

        self.refresh(url=self._client._build_url('property', property_id=self.id))

    def _parse_validators(self):
        """Parse the validator in the options to validators."""
        self._validators = []
        validators_json = self._options.get('validators')
        for validator_json in validators_json:
            self._validators.append(PropertyValidator.parse(json=validator_json))

    def _dump_validators(self):
        """Dump the validators as json inside the _options dictionary with the key `validators`."""
        if hasattr(self, '_validators'):
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
    def is_valid(self):
        # type: () -> Union[bool, None]
        """Determine if the value in the property is valid.

        If the value of the property is validated as 'valid', than returns a True, otherwise a False.
        When no validators are configured, returns a None. It checks against all configured validators
        and returns a single boolean outcome.

        :returns: True when the `value` is valid
        :rtype: bool or None
        """
        if not hasattr(self, '_validators'):
            return None
        else:
            self.validate(reason=False)
            if all([vr is None for vr in self._validation_results]):
                return None
            else:
                return all(self._validation_results)

    @property
    def is_invalid(self):
        # type: () -> Union[bool, None]
        """Determine if the value in the property is invalid.

        If the value of the property is validated as 'invalid', than returns a True, otherwise a False.
        When no validators are configured, returns a None. It checks against all configured validators
        and returns a single boolean outcome.

        :returns: True when the `value` is invalid
        :rtype: bool
        """
        if self.is_valid is not None:
            return not self.is_valid
        else:
            return None

    def validate(self, reason=True):
        # type: (bool) -> list
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
        self._validation_results = [validator.is_valid(self._value) for validator in getattr(self, '_validators')]
        self._validation_reasons = [validator.get_reason() for validator in getattr(self, '_validators')]

        if reason:
            return list(zip(self._validation_results, self._validation_reasons))
        else:
            return self._validation_results
