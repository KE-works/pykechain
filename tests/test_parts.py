import os
from unittest import TestCase

from betamax import Betamax

import pykechain
from pykechain import Client
from pykechain.models import PartSet, Scope
from .utils import TEST_TOKEN, get_method_name, TEST_URL, TEST_SCOPE_ID


class TestPartAPI(TestCase):
    """
    tests the part API
    """
    def setUp(self):
        self.client = Client(url=TEST_URL)

        with Betamax.configure() as config:
            config.cassette_library_dir = os.path.join(os.path.dirname(__file__), 'cassettes')

    def test_retrieve_part(self):
        with Betamax(self.client.session) as vcr:
            vcr.use_cassette(get_method_name())

            self.client.login(token=TEST_TOKEN)

            bike_part = self.client.parts(name="Bike")

            print(self.client._build_url("parts", params = dict(name="Bike")))
            self.assertEqual(type(bike_part), PartSet)
            self.assertEqual(bike_part.name, "Bike")
            self.assertEqual(bike_part.bucket, 1)


    def test_get_scope(self):
        with Betamax(self.client.session) as vcr:
            vcr.use_cassette(get_method_name())

            self.client.login(token=TEST_TOKEN)

            scope = self.client.scope(id=TEST_SCOPE_ID)
            self.assertEqual(type(scope), Scope)
            self.assertEqual(scope.name, "Bike Project")
            self.assertEqual(scope.id, TEST_SCOPE_ID)
