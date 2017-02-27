from pykechain.models import Property, Part


class ReferenceProperty(Property):
    """A virtual object representing a KE-chain reference property."""

    @property
    def value(self):
        """Value of a reference property.

        :return: Part or None
        """
        if not self._value:
            return None

        return self._client.part(pk=self._value['id'])

    @value.setter
    def value(self, value):
        if value and not isinstance(value, Part):
            raise ValueError("Reference must be a Part")

        part_id = value.id if value else None

        self._value = self._put_value(part_id)
