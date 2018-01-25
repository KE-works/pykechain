from six import text_type

from pykechain.models.part import Part
from pykechain.models.property import Property


class ReferenceProperty(Property):
    """A virtual object representing a KE-chain reference property."""

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

        return self._client.part(pk=self._value['id'])

    @value.setter
    def value(self, value):
        if isinstance(value, Part):
            part_id = value.id
        elif isinstance(value, (type(None), text_type)):
            # tested against a six.text_type (found in the requests' urllib3 package) for unicode conversion in py27
            part_id = value
        else:
            raise ValueError("Reference must be a Part, Part id or None. type: {}".format(type(value)))

        self._value = self._put_value(part_id)

    def choices(self):
        """Retrieve the parts that you can reference for this `ReferenceProperty`.

        This method makes 2 API calls: 1) to retrieve the referenced model, and 2) to retrieve the instances of
        that model.

        :return: the :class:`Part`'s that can be referenced as a :class:`~pykechain.model.PartSet`.
        :raises APIError: When unable to load and provide the choices

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
