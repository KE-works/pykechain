from six import text_type

from pykechain.models.part import Part
from pykechain.models.property import Property
from pykechain.utils import is_uuid


class MultiReferenceProperty(Property):
    """A virtual object representing a KE-chain multi-references property.

    .. versionadded:: 1.14
    """

    def __init__(self, json, **kwargs):
        """Construct a MultiReferenceProperty from a json object."""
        super(MultiReferenceProperty, self).__init__(json, **kwargs)

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
        >>> isinstance(wheels_ref_property, MultiReferenceProperty)
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
            ids = [v.get('id') for v in self._value]
            self._cached_values = list(self._client.parts(id__in=','.join(ids), category=None))
        return self._cached_values

    @value.setter
    def value(self, value):
        value_to_set = []
        if isinstance(value, (list, tuple)):
            for item in value:
                if isinstance(item, Part):
                    value_to_set.append(item.id)
                elif isinstance(item, text_type) and is_uuid(item):
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

        # we replace the current choices!
        self._value = self._put_value(value_to_set)

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
        referenced_model = property_model.value and property_model.value[0]  # list of seleceted models is always 1
        possible_choices = self._client.parts(model=referenced_model)  # makes multiple parts call

        return possible_choices
