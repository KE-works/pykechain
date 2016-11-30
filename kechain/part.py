from kechain.structure import Structure
from kechain.property import Property


class Part(Structure):

    def __init__(self):
        super().__init__()
        self._properties = []

    @property
    def properties(self):
        return self._properties

    def find_property(self, property_name):
        return next(prop for prop in self.properties if prop.name == property_name)

    @classmethod
    def from_dict(cls, data):
        obj = super().from_dict(data)

        obj._properties = [Property.from_dict(prop_data) for prop_data in data['properties']]

        return obj

    def __repr__(self):
        props = ', '.join('{0}: {1}'.format(p.name, p.value) for p in self.properties)

        return 'Part({0}, {1})'.format(self.name, props)
