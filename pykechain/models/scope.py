from pykechain.models import Base


class Scope(Base):

    def __init__(self, json, **kwargs):
        super(Scope, self).__init__(json, **kwargs)

        self.bucket = json.get('bucket', {})

    def parts(self, *args, **kwargs):
        return self._client.parts(*args, bucket=self.bucket.get('id'), **kwargs)

    def part(self, *args, **kwargs):
        return self._client.part(*args, bucket=self.bucket.get('id'), **kwargs)

    def model(self, *args, **kwargs):
        return self._client.model(*args, bucket=self.bucket.get('id'), **kwargs)
