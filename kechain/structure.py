

class Structure(object):

    def __init__(self):
        self._id = None
        self._name = None
        self._dirty = False

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def dirty(self):
        """Boolean indicating if the property is modified."""
        return self._dirty

    @classmethod
    def from_dict(cls, data):
        obj = cls()

        obj._id = data['id']
        obj._name = data['name']

        return obj
