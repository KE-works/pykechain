import os
from unittest import TestCase

from betamax import Betamax

from pykechain import Client
from tests.utils import TEST_TOKEN, TEST_URL

with Betamax.configure() as config:
    config.cassette_library_dir = os.path.join(os.path.dirname(__file__), 'cassettes')
    config.define_cassette_placeholder('<AUTH_TOKEN>', TEST_TOKEN)


class TestBetamax(TestCase):

    @property
    def cassette_name(self):
        cls = getattr(self, '__class__')
        test = self._testMethodName
        return '{0}.{1}'.format(cls.__name__, test)

    def setUp(self):
        self.client = Client(url=TEST_URL)

        if TEST_TOKEN:
            self.client.login(token=TEST_TOKEN)

        self.recorder = Betamax(session=self.client.session)
        self.recorder.use_cassette(self.cassette_name)
        self.recorder.start()

    def tearDown(self):
        self.recorder.stop()
