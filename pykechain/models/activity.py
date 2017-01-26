from pykechain.exceptions import APIError
from pykechain.models import Base


class Activity(Base):
    """A virtual object representing a KE-chain activity."""

    def __init__(self, json, **kwargs):
        """Construct an Activity from a json object."""
        super(Activity, self).__init__(json, **kwargs)

        self.scope = json.get('scope')
        self.association = json.get('association_id')

    def parts(self, *args, **kwargs):
        """Retrieve parts belonging to this activity.

        See :class:`pykechain.Client.parts` for available parameters.
        """
        return self._client.parts(*args, activity=self.id, **kwargs)

    def configure(self, inputs, outputs):
        """Configure activity input and output.

        :param inputs: iterable of input property models
        :param outputs: iterable of output property models
        :raises: APIError
        """
        url = self._client._build_url('association', association_id=self.association)

        r = self._client._request('PUT', url, json={
            'inputs': [p.id for p in inputs],
            'outputs': [p.id for p in outputs]
        })

        if r.status_code != 200:  # pragma: no cover
            raise APIError("Could not configure activity")

    def delete(self):
        """Delete this activity."""
        r = self._client._request('DELETE', self._client._build_url('activity', activity_id=self.id))

        if r.status_code != 204:
            raise APIError("Could not delete activity: {} with id {}".format(self.name, self.id))

    def create_activity(self, *args, **kwargs):
        """Create a new activity belonging to this subprocess.

        See :class:`pykechain.Client.create_activity` for available parameters.
        """
        return self._client.create_activity(self.id, *args, **kwargs)
