from pykechain.exceptions import APIError
from pykechain.models.property import Property


class SelectListProperty(Property):
    """A select list property that needs to update its options."""

    def __init__(self, json, **kwargs):
        """Construct a Property from a json object."""
        super(SelectListProperty, self).__init__(json, **kwargs)
        self._options = self._json_data.get('options').get('value_choices')

    @property
    def options(self):
        """List of options of this property to select from."""
        return self._options

    @options.setter
    def options(self, options_list):
        """
        Set the options of the select list property if the property is a property model.

        Will raise an exception if the property is not a model. Will also raise an exception if the list is of
        incorrect form and contains non string, floats or integers.

        :param options_list: list of options to set, using only strings, integers and floats in the list.
        :raises: APIError, AssertionError

        Example
        -------

        >>> a_model = project.model('Model')
        >>> select_list_property = a_model.property('a_select_list_property')

        Get the list of options on the property
        >>> select_list_property.options
        ['1', '2', '3', '4']

        Update the list of options
        >>> select_list_property.options = [1,3,5,"wow"]
        """
        if not isinstance(options_list, list):
            raise APIError("The list of options should be a list")
        if self._json_data.get('category') != 'MODEL':
            raise APIError("We can only update the options list of the model of this property. The model of this "
                           "property has id '{}'".format(self._json_data.get('model')))

        # stringify the options list
        options_list = list(map(str, options_list))
        if not self._options or set(options_list) != set(self._options):
            self._put_options(options_list=options_list)
            self._options = options_list

    def _put_options(self, options_list):
        """Save the options to the database.

        Will check for the correct form of the data.

        :param options_list: list of options to set.
        :raises APIError
        """
        url = self._client._build_url('property', property_id=self.id)
        response = self._client._request('PUT', url, json={'options': {"value_choices": options_list}})

        if response.status_code != 200:  # pragma: no cover
            raise APIError("Could not update property value. Response: {}".format(str(response)))
