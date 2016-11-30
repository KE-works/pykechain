from kechain.structure import Structure


class Property(Structure):

    def __init__(self):
        super().__init__()
        self._value = None

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
        obj = super().from_dict(data)

        obj._value = data['value']

        return obj

    def __repr__(self):
        return 'Property({0}, {1})'.format(self.name, self.value)
