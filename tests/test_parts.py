import os
from unittest import TestCase
from unittest import skip

from betamax import Betamax

from pykechain import Client
from pykechain.models import Scope
from .utils import TEST_TOKEN, get_method_name, TEST_URL, TEST_SCOPE_ID


class TestPartAPI(TestCase):
    """
    tests the part API
    """

    def setUp(self):
        self.client = Client(url=TEST_URL)

        with Betamax.configure() as config:
            config.cassette_library_dir = os.path.join(os.path.dirname(__file__), 'cassettes')

    @skip('TODO: fix bug that part by name retrieval for users < superuser')
    def test_retrieve_part(self):
        with Betamax(self.client.session) as vcr:
            vcr.use_cassette(get_method_name())

            self.client.login(token=TEST_TOKEN)

            bike_parts = self.client.parts(name="Bike")

            # TODO: fix this bug that a normal member or manager cannot retrieve part by name
            self.assertEqual(len(bike_parts), 1)

    def test_get_scope(self):
        with Betamax(self.client.session) as vcr:
            vcr.use_cassette(get_method_name())

            self.client.login(token=TEST_TOKEN)

            scope = self.client.scope(id=TEST_SCOPE_ID)
            self.assertEqual(type(scope), Scope)
            self.assertEqual(scope.name, "Bike Project")
            self.assertEqual(scope.id, TEST_SCOPE_ID)
