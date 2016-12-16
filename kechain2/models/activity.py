from kechain2.models import Base


class Activity(Base):

    def __init__(self, json):
        super(Activity, self).__init__(json)

        self.scope = json.get('scope')

    def parts(self, *args, **kwargs):
        from kechain2.api import parts

        return parts(*args, activity=self.id, **kwargs)
