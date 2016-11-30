

class PartSet(object):

    def __init__(self, parts):
        self._parts = list(parts)

    def __iter__(self):
        return self._parts.__iter__()

    def __getitem__(self, key):
        return [p.value for p in self.find_properties(key)]

    def find_properties(self, name):
        return [p.find_property(name) for p in self]
