

class PartSet(object):

    def __init__(self, parts):
        self._parts = list(parts)

    def __iter__(self):
        return self._parts.__iter__()
