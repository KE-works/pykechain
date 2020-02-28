from jsonschema import validate

from pykechain.enums import Category
from pykechain.exceptions import APIError, IllegalArgumentError, _DeprecationMixin
from pykechain.models.property2 import Property2
from pykechain.models.validators.validator_schemas import options_json_schema


class SelectListProperty(Property2):
    """A select list property that needs to update its options."""

    def __init__(self, json, **kwargs):
        """Construct a Property from a json object."""
        super().__init__(json, **kwargs)
        self._value_choices = json.get('value_options').get('value_choices')

    @property
    def value(self):
        """Retrieve the data value of a property.

        Setting this value will immediately update the property in KE-chain.
        The value should be in the list of options.

        :raises APIError: when unable to set the value or the value is not in the list of options
        """
        return self._value

    @value.setter
    def value(self, value):
        if value not in self.options and value is not None:
            raise APIError('The new value `{}` of the single select list property should be in the list of '
                           'options `{}`'.format(value, self.options))
        if self._put_value(value):
            self._value = value
            self._json_data['value'] = value

    @property
    def options(self):
        """
        Get or set the options of the select list property if the property is a property model.

        Will raise an exception if the property is not a model. Will also raise an exception if the list is of
        incorrect form and contains non string, floats or integers.

        :param options_list: list of options to set, using only strings, integers and floats in the list.
        :type options_list: list
        :raises APIError: When unable to set the list of options
        :raises IllegalArgumentError: When the options_list is not in the right form or type, or the property is not
                                      a property model (:class:`Property` with category MODEL)

        Example
        -------
        >>> a_model = project.model('Model')
        >>> select_list_property = a_model.property('a_select_list_property')

        Get the list of options on the property
        >>> select_list_property.options
        ['1', '2', '3', '4']

        Update the list of options
        >>> select_list_property.options = [1,3,5,"wow"]

        List of options of this property to select from.

        """
        return self._value_choices

    @options.setter
    def options(self, options_list):
        if not isinstance(options_list, list):
            raise IllegalArgumentError("The list of options should be a list")
        if self._json_data.get('category') != Category.MODEL:
            raise IllegalArgumentError("We can only update the options list of the model of this property. The "
                                       "model of this property has id '{}'".format(self._json_data.get('model')))

        # stringify the options list
        options_list = list(map(str, options_list))

        # check if the options are not already set and indeed different
        if not self._value_choices or set(options_list) != set(self._value_choices):
            self._put_options(options_list=options_list)
            self._value_choices = options_list

    def _put_options(self, options_list):
        """Save the options to KE-chain.

        Makes a single API call.

        :param options_list: list of options to set.
        :raises APIError: when unable to update the options
        """
        new_options = self._options.copy()  # make a full copy of the dict not to only link it and update dict in place
        new_options.update({"value_choices": options_list})
        validate(new_options, options_json_schema)

        url = self._client._build_url('property2', property_id=self.id)
        response = self._client._request('PUT', url, json={'value_options': new_options})

        if response.status_code != 200:  # pragma: no cover
            raise APIError("Could not update property value. Response: {}".format(str(response)))
        else:
            self._options = new_options  # save the new options as the options


class SelectListProperty2(SelectListProperty, _DeprecationMixin):
    """A select list property that needs to update its options."""

    pass
