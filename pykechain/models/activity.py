from typing import Any  # flake8: noqa

from pykechain.models.base import Base


class Activity(Base):
    """A virtual object representing a KE-chain activity."""

    def __init__(self, json, **kwargs):
        # type: (dict, **Any) -> None
        """Construct an Activity from a json object."""
        super(Activity, self).__init__(json, **kwargs)

        self.scope = json.get('scope')

    def parts(self, *args, **kwargs):
        """Retrieve parts belonging to this activity.

        See :class:`pykechain.Client.parts` for available parameters.
        """
        return self._client.parts(*args, activity=self.id, **kwargs)
