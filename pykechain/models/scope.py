from typing import Any  # flake8: noqa

from pykechain.enums import Multiplicity
from pykechain.models.base import Base


class Scope(Base):
    """A virtual object representing a KE-chain scope."""

    def __init__(self, json, **kwargs):
        # type: (dict, **Any) -> None
        """Construct a scope from provided json data."""
        super(Scope, self).__init__(json, **kwargs)

        self.bucket = json.get('bucket', {})
        self.process = json.get('process')

    def __repr__(self):
        return "<pyke Scope '{}' id {}>".format(self.name, self.id[-8:])

    def parts(self, *args, **kwargs):
        """Retrieve parts belonging to this scope.

        See :class:`pykechain.Client.parts` for available parameters.
        """
        return self._client.parts(*args, bucket=self.bucket.get('id'), **kwargs)

    def part(self, *args, **kwargs):
        """Retrieve a single part belonging to this scope.

        See :class:`pykechain.Client.part` for available parameters.
        """
        return self._client.part(*args, bucket=self.bucket.get('id'), **kwargs)

    def create_model(self, parent, name, multiplicity = Multiplicity.ZERO_MANY):
        """Create a single part model in this scope.
        
        See :class:`pykechain.Client.create_model` for available parameters.        
        """
        return self._client.create_model(parent, name, multiplicity=Multiplicity.ZERO_MANY)

    def model(self, *args, **kwargs):
        """Retrieve a single model belonging to this scope.

        See :class:`pykechain.Client.model` for available parameters.
        """
        return self._client.model(*args, bucket=self.bucket.get('id'), **kwargs)

    def activities(self, *args, **kwargs):
        """Retrieve activities belonging to this scope.

        See :class:`pykechain.Client.activities` for available parameters.
        """
        return self._client.activities(*args, scope=self.id, **kwargs)

    def activity(self, *args, **kwargs):
        """Retrieve a single activity belonging to this scope.

        See :class:`pykechain.Client.activity` for available parameters.
        """
        return self._client.activity(*args, scope=self.id, **kwargs)

    def create_activity(self, *args, **kwargs):
        """Create a new activity belonging to this scope.

        See :class:`pykechain.Client.create_activity` for available parameters.
        """
        return self._client.create_activity(self.process, *args, **kwargs)
