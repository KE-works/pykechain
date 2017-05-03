from requests.packages.urllib3.packages.six import text_type

from pykechain.models.property import Property
from pykechain.models.part import Part


class ReferenceProperty(Property):
    """A virtual object representing a KE-chain reference property."""

    @property
    def value(self):
        """Value of a reference property.

        You can set the reference with a Part, Part id or None value.
        Ensure that the model of the provided part, matches the configured model

        :return: Part or None

        Example
        -------
        # get the wheel reference property
        >>> part = project.part('Bike')
        >>> material_ref_property = part.property('Material Selection')
        >>> type(material_ref_property) == ReferenceProperty
        True

        # the value either returns a Part or is None if not set (yet)
        >>> type(material_ref_property.value) in (Part, None)
        True

        # get the selection of material instances cantaining the word material (icontains is for case-insensitive)
        >>> material_choices = project.parts(icontains='material')

        # choose random material option
        >>> from random import choice
        >>> chosen_material = choice(material_choices)

        # set chosen material
        # 1: provide the part
        >>> material_ref_property.value = chosen_material

        # 2: provide the id
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
