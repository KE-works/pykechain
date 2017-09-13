import sys
from unittest import TestCase

import os
from betamax import Betamax

from pykechain import Client
from tests.utils import TEST_TOKEN, TEST_URL, TEST_SCOPE_NAME

with Betamax.configure() as config:
    config.cassette_library_dir = os.path.join(os.path.dirname(__file__), 'cassettes')
    config.define_cassette_placeholder('<API_URL>', TEST_URL)
    config.define_cassette_placeholder('<AUTH_TOKEN>', TEST_TOKEN)


class TestBetamax(TestCase):
    @property
    def cassette_name(self):
        cls = getattr(self, '__class__')
        test = self._testMethodName
        return '{0}.{1}'.format(cls.__name__, test)

    def setUp(self):
        self.client = Client(url=TEST_URL)
        # for debugging:
        # print('--> ENVIRONMENT VARS: {}'.format(os.environ))

        if TEST_TOKEN:
            self.client.login(token=TEST_TOKEN)

        self.recorder = Betamax(session=self.client.session)
        self.recorder.use_cassette(self.cassette_name)
        self.recorder.start()
        self.project = self.client.scope(TEST_SCOPE_NAME)

    def tearDown(self):
        self.recorder.stop()

    def assertRaisesRegex(self, expected_exception, expected_regex,
                          *args, **kwargs):
        if sys.version_info.major < 3:
            return self.assertRaisesRegexp(expected_exception, expected_regex, *args, **kwargs)
        else:
            return super(__class__, self).assertRaisesRegex(expected_exception, expected_regex,
                                                            *args, **kwargs)
