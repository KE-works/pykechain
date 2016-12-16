from kechain2.models import Base


class Scope(Base):

    def __init__(self, json):
        super(Scope, self).__init__(json)

        self.bucket = json.get('bucket', {})

    def parts(self, *args, **kwargs):
        from kechain2.api import parts

        return parts(*args, bucket=self.bucket.get('id'), **kwargs)

    def part(self, *args, **kwargs):
        from kechain2.api import part

        return part(*args, bucket=self.bucket.get('id'), **kwargs)

    def model(self, *args, **kwargs):
        from kechain2.api import model

        return model(*args, bucket=self.bucket.get('id'), **kwargs)