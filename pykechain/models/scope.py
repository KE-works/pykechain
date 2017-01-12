from pykechain.models import Base


class Scope(Base):
    """A virtual object representing a KE-chain scope."""

    def __init__(self, json, **kwargs):
        """Construct a scope from provided json data."""
        super(Scope, self).__init__(json, **kwargs)

        self.bucket = json.get('bucket', {})

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

    def model(self, *args, **kwargs):
        """Retrieve a single model belonging to this scope.

        See :class:`pykechain.Client.model` for available parameters.
        """
        return self._client.model(*args, bucket=self.bucket.get('id'), **kwargs)
