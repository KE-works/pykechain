from pykechain.models import Base


class Activity(Base):

    def __init__(self, json, **kwargs):
        super(Activity, self).__init__(json, **kwargs)

        self.scope = json.get('scope')

    def parts(self, *args, **kwargs):
        return self._client.parts(*args, activity=self.id, **kwargs)
