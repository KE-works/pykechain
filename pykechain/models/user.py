from .base import Base


class User(Base):
    """A virtual object representing a KE-chain user."""

    def __init__(self, json, **kwargs):
        """Construct a scope from provided json data."""
        super(User, self).__init__(json, **kwargs)

        self.username = self._json_data.get('username', '')
        self.name = self.username
        self.id = self._json_data.get('pk', '')

    def __repr__(self):  # pragma: no cover
        return "<pyke {} '{}' id {}>".format(self.__class__.__name__, self.username, self.id)
