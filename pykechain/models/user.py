from .base import Base

class User(Base):
    """A virtual object representing a KE-chain user."""

    def __init__(self, json, **kwargs):
        # type: (dict, **Any) -> None
        """Construct a scope from provided json data."""
        super(User, self).__init__(json, **kwargs)

        self.username = self._json_data.get('username', '')
        self.id = self._json_data.get('pk', '')
