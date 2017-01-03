from pykechain import Client
from pykechain.models.base import Base


class TestBase(object):

    json = {
        'id': '123',
        'name': 'test'
    }

    def test_id(self):
        obj = Base(self.json)

        assert obj.id == '123'

    def test_name(self):
        obj = Base(self.json)

        assert obj.name == 'test'

    def test_default_client(self):
        obj = Base(self.json)

        from pykechain.api import client

        assert obj._client is client

    def test_given_client(self):
        client = Client()

        obj = Base(self.json, client)

        assert obj._client is client
