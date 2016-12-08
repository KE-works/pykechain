

class PartSet(object):

    def __init__(self, parts):
        self._parts = list(parts)

    def __iter__(self):
        return self._parts.__iter__()

    def __len__(self):
        return len(self._parts)

    def __getitem__(self, k):
        assert isinstance(k, int), "[not implemented] non-integer indexing in PartSet"

        return self._parts[k]
