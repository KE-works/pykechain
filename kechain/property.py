
class Property(object):
    id = None
    name = None
    value = None
    _dirty = False

    @classmethod
    def from_dict(cls, data):
        property = cls()

        property.id = data['id']
        property.name = data['name']
        property.value = data['value']

        return property

    def set_value(self, value):
        if value != self.value:
            self.value = value
            self._dirty = True

    def __repr__(self):
        return 'Property({0}, {1})'.format(self.name, self.value)
