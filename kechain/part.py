from kechain.property import Property


class Part(object):
    id = None
    name = None
    properties = []
    _dirty = False

    @classmethod
    def from_dict(cls, data):
        part = cls()

        part.id = data['id']
        part.name = data['name']

        part.properties = [Property.from_dict(prop_data) for prop_data in data['properties']]

        return part

    def __repr__(self):
        props = ', '.join('{0}: {1}'.format(p.name, p.value) for p in self.properties)

        return 'Part({0}, {1})'.format(self.name, props)
