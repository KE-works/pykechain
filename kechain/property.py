
class Property(object):
    id = None
    name = None

    def __init__(self):
        self._dirty = False
        self._value = None

    @property
    def dirty(self):
        """Boolean indicating if the property is modified."""
        return self._dirty

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value != self._value:
            self._value = value
            self._dirty = True

    @classmethod
    def from_dict(cls, data):
        prop = cls()

        prop.id = data['id']
        prop.name = data['name']
        prop._value = data['value']

        return prop

    def __repr__(self):
        return 'Property({0}, {1})'.format(self.name, self.value)
