from unittest import TestCase

from pykechain import Client
from pykechain.models.base import Base


class TestBase(TestCase):

    json = {
        'id': '123',
        'name': 'test'
    }

    def test_id(self):
        obj = Base(self.json, None)

        self.assertEqual(obj.id , '123')

    def test_name(self):
        obj = Base(self.json, None)

        self.assertEqual( obj.name ,'test')

    def test_given_client(self):
        client = Client()

        obj = Base(self.json, client)

        self.assertEqual(obj._client, client)
        self.assertIsInstance(obj._client, Client)
