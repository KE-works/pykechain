from six import text_type, string_types

from pykechain.enums import Category, FilterType, PropertyType
from pykechain.exceptions import IllegalArgumentError
from pykechain.models.part2 import Part2
from pykechain.models.property2 import Property2
from pykechain.utils import is_uuid


class MultiReferenceProperty2(Property2):
    """A virtual object representing a KE-chain multi-references property.

    .. versionadded:: 1.14
    """

    def __init__(self, json, **kwargs):
        """Construct a MultiReferenceProperty from a json object."""
        super(MultiReferenceProperty2, self).__init__(json, **kwargs)

        self._cached_values = None

    @property
    def value(self):
        """Value of a reference property.

        You can set the reference with a Part, Part id or None value.
        Ensure that the model of the provided part, matches the configured model

        :return: a :class:`Part` or None
        :raises APIError: When unable to find the associated :class:`Part`

        Example
        -------
        Get the wheel reference property

        >>> part = project.part('Bike')
        >>> wheels_ref_property = part.property('Wheels')
        >>> isinstance(wheels_ref_property, MultiReferenceProperty2)
        True

        The value returns a list of Parts or is an empty list

        >>> type(wheels_ref_property.value) in (list, tuple)
        True

        Get the selection of wheel instances:

        >>> wheel_choices = wheels_ref_property.choices()

        Choose random wheel from the wheel_choices:

        >>> from random import choice
        >>> wheel_choice_1 = choice(wheel_choices)
        >>> wheel_choice_2 = choice(wheel_choices)

        Set chosen wheel
        1: provide a single wheel:

        >>> wheels_ref_property.value = [wheel_choice_1]

        2: provide multiple wheels:

        >>> wheels_ref_property.value = [wheel_choice_1, wheel_choice_2]

        """
        if not self._value:
            return None
        if not self._cached_values and isinstance(self._value, (list, tuple)):
            assert all([isinstance(v, dict) for v in self._value]), \
                "Expect all elements in the _value to be a dict with 'name' and 'id', got '{}'".format(self._value)
            ids = [v.get('id') for v in self._value]
            # TODO: this will change when the configured model is put in the value_options. Now we configure a single
            # ...   part_model_id in the multirefproperty_model.value as
            if self.category == Category.MODEL and len(ids) == 1:
                self._cached_values = [self._client.part(pk=ids[0], category=None)]
            elif self.category == Category.INSTANCE:
                referred_partmodels = self.model().value
                if referred_partmodels:
                    referred_partmodel = referred_partmodels[0]  # get the only one, which is the right part_model
                else:
                    referred_partmodel = None
                self._cached_values = list(self._client.parts(id__in=','.join(ids),
                                                              model=referred_partmodel,
                                                              category=None))
        return self._cached_values

    @value.setter
    def value(self, value):
        value_to_set = []
        if isinstance(value, (list, tuple)):
            for item in value:
                if isinstance(item, Part2):
                    value_to_set.append(item.id)
                elif isinstance(item, (string_types, text_type)) and is_uuid(item):
                    # tested against a six.text_type (found in the requests' urllib3 package) for unicode
                    # conversion in py27
                    value_to_set.append(item)
                else:
                    raise ValueError("Reference must be a Part, Part id or None. type: {}".format(type(item)))
        elif isinstance(value, type(None)):
            # clear out the list
            value_to_set = None
        else:
            raise ValueError(
                "Reference must be a list (or tuple) of Part, Part id or None. type: {}".format(type(value)))

        # we replace the current choices in the _put_value
        self._put_value(value_to_set)

    def choices(self):
        """Retrieve the parts that you can reference for this `MultiReferenceProperty`.

        This method makes 2 API calls: 1) to retrieve the referenced model, and 2) to retrieve the instances of
        that model.

        :return: the :class:`Part`'s that can be referenced as a :class:`~pykechain.model.PartSet`.
        :raises APIError: When unable to load and provide the choices

        Example
        -------
        >>> property = project.part('Bike').property('a_multi_reference_property')
        >>> reference_part_choices = property.choices()

        """
        # from the reference property (instance) we need to get the value of the reference property in the model
        # in the reference property of the model the value is set to the ID of the model from which we can choose parts
        model_parent_part = self.part.model()  # makes single part call
        property_model = model_parent_part.property(self.name)
        referenced_model = property_model.value and property_model.value[0]  # list of selected models is always 1
        possible_choices = self._client.parts(model=referenced_model)  # makes multiple parts call

        return possible_choices

    def set_prefilters(self, property_models, values, filters_type=FilterType.CONTAINS, overwrite=False):
        """

        :param property_models:
        :param values:
        :param filters_type:
        :param overwrite:
        :return:
        """
        if any(len(lst) != len(property_models) for lst in [values, filters_type]):
            raise IllegalArgumentError('The lists of "property_models", "values" and "filters_type" should be the '
                                       'same length')
        if not overwrite:
            initial_prefilters = self._options.get('prefilters', {})
            list_of_prefilters = initial_prefilters.get('property_value', [])
            if list_of_prefilters:
                list_of_prefilters = list_of_prefilters.split(',')
        else:
            list_of_prefilters = list()

        for property_model in property_models:
            index = property_models.index(property_model)
            if not isinstance(property_model, Property2):
                if is_uuid(property_model):
                    property_model = self._client.property(id=property_model, category=Category.MODEL)
                else:
                    raise IllegalArgumentError('Pre-filters can only be set on `Property` models or their UUIDs, '
                                               'found type "{}"'.format(type(property_model)))

            if property_model.category != Category.MODEL:
                raise IllegalArgumentError('Pre-filters can only be set on property models, found category "{}"'
                                           'on property "{}"'.format(property_model.category, property_model.name))
            # TODO when a property is freshly created, the property has no "part_id" key in json_data.
            elif self.value[0].id != property_model._json_data.get('part_id', self.value[0].id):
                raise IllegalArgumentError(
                    'Pre-filters can only be set on properties belonging to the reference Part model, found referenced '
                    'Part model "{}" and Properties belonging to "{}"'.format(
                        self.value[0].name, property_model.part.name))
            else:
                property_id = property_model.id
                if property_model.type == PropertyType.DATETIME_VALUE:
                    datetime_value = values[index]
                    # TODO really not elegant way to deal with DATETIME. Issue is that the value is being double
                    #  encoded (KEC-20504)
                    datetime_value = "{}-{}-{}T00%253A00%253A00.000Z".format(datetime_value.year,
                                                                             str(datetime_value.month).rjust(2, '0'),
                                                                             str(datetime_value.day).rjust(2, '0'))
                    new_prefilter_list = [property_id, datetime_value, filters_type[index]]
                    new_prefilter = '%3A'.join(new_prefilter_list)
                else:
                    new_prefilter_list = [property_id, str(values[index]), filters_type[index]]
                    new_prefilter = ':'.join(new_prefilter_list)
                list_of_prefilters.append(new_prefilter)

        initial_propmodels_excl = self._options.get('propmodels_excl', [])
        options = dict()
        options['prefilters'] = {'property_value': ','.join(list_of_prefilters) if list_of_prefilters else {}}
        options['propmodels_excl'] = initial_propmodels_excl
        options['scope_id'] = self.value[0]._json_data["scope_id"]

        self.edit(options=options)
        return
