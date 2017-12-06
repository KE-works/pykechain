from six import text_type

from pykechain.models.part import Part
from pykechain.models.property import Property
from pykechain.utils import is_uuid


class MultiReferenceProperty(Property):
    """A virtual object representing a KE-chain multi-references property."""

    def __init__(self, json, **kwargs):
        # type: (dict, **Any) -> None
        """Construct a MultiReferenceProperty from a json object."""
        super(MultiReferenceProperty, self).__init__(json, **kwargs)

        self._cached_values = None

    @property
    def value(self):
        """Value of a reference property.

        You can set the reference with a Part, Part id or None value.
        Ensure that the model of the provided part, matches the configured model

        :return: Part or None

        Example
        -------
        Get the wheel reference property

        >>> part = project.part('Bike')
        >>> material_ref_property = part.property('Material Selection')
        >>> isinstance(material_ref_property, ReferenceProperty)
        True

        The value either returns a Part or is None if not set (yet)

        >>> type(material_ref_property.value) in (Part, None)
        True

        Get the selection of material instances containing the word material (icontains is for case-insensitive)

        >>> material_choices = project.parts(icontains='material')

        Choose random material option

        >>> from random import choice
        >>> chosen_material = choice(material_choices)

        Set chosen material
        1: provide the part

        >>> material_ref_property.value = chosen_material

        2: provide the id

        >>> material_ref_property.value = chosen_material.id

        """
        if not self._value:
            return None
        if not self._cached_values and isinstance(self._value, (list, tuple)):
            self._cached_values = list(self._client.parts(id__in=[str(v.id) for v in self._value]))
        return self._cached_values

    @value.setter
    def value(self, value):
        if isinstance(value, (list, tuple)):
            for item in value:
                if isinstance(item, Part):
                    item = item.id
                elif isinstance(item, text_type) and is_uuid(item):
                    # tested against a six.text_type (found in the requests' urllib3 package) for unicode conversion in py27
                    pass  # item = item
                else:
                    raise ValueError("Reference must be a Part, Part id or None. type: {}".format(type(item)))
        elif isinstance(value, type(None)):
            value = None
        else:
            raise ValueError(
                "Reference must be a list (or tuple) of Part, Part id or None. type: {}".format(type(value)))

        # we replace the current choices!
        self._value = self._put_value(value)

    def choices(self):
        """Retrieve the parts that you can reference for this `ReferenceProperty`.

        :return: the parts that can be referenced as :class:`pykechain.model.PartSet`.
        :raises: PropertyTypeError

        Example
        -------

        >>> property = project.part('Bike').property('RefTest')
        >>> reference_part_choices = property.choices()

        """
        # from the reference property (instance) we need to get the value of the reference property in the model
        # in the reference property of the model the value is set to the ID of the model from which we can choose parts
        model_parent_part = self.part.model()  # makes single part call
        property_model = model_parent_part.property(self.name)
        referenced_model = self._client.model(pk=property_model._value['id'])  # makes single part call
        possible_choices = self._client.parts(model=referenced_model)  # makes multiple parts call

        return possible_choices
