import os
from unittest import TestCase

from betamax import Betamax

from pykechain import Client
from tests.utils import TEST_TOKEN, TEST_URL, TEST_SCOPE_NAME, TEST_RECORD

with Betamax.configure() as config:
    config.cassette_library_dir = os.path.join(os.path.dirname(__file__), 'cassettes')
    config.define_cassette_placeholder('<API_URL>', TEST_URL)
    config.define_cassette_placeholder('<AUTH_TOKEN>', TEST_TOKEN)


class TestBetamax(TestCase):
    find_project = True

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
        # TODO: turn off recording for travis CI
        self.recorder.use_cassette(self.cassette_name, record=TEST_RECORD)
        self.recorder.start()

        if self.find_project:
            self.project = self.client.scope(TEST_SCOPE_NAME)

    def tearDown(self):
        self.recorder.stop()
