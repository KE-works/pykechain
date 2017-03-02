from pykechain.models import Property, Part


class ReferenceProperty(Property):
    """A virtual object representing a KE-chain reference property."""

    @property
    def value(self):
        """Value of a reference property.

        You can set the reference with a Part, Part id or None value.

        :return: Part or None
        """
        if not self._value:
            return None

        return self._client.part(pk=self._value['id'])

    @value.setter
    def value(self, value):
        if isinstance(value, Part):
            part_id = value.id
        elif isinstance(value, (type(None), str)):
            part_id = value
        else:
            raise ValueError("Reference must be a Part, Part id or None")

        self._value = self._put_value(part_id)
