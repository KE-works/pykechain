import os
from unittest import TestCase

import six
from betamax import Betamax

if six.PY2:
    from test.test_support import EnvironmentVarGuard
elif six.PY3:
    from test.support import EnvironmentVarGuard

from pykechain import Client
from tests.utils import TEST_TOKEN, TEST_SCOPE_NAME, TEST_URL, TEST_RECORD_CASSETTES, TEST_SCOPE_ID

with Betamax.configure() as config:
    config.cassette_library_dir = os.path.join(os.path.dirname(__file__), 'cassettes')
    config.define_cassette_placeholder('<API_URL>', TEST_URL)
    config.define_cassette_placeholder('<AUTH_TOKEN>', TEST_TOKEN)


class SixTestCase(TestCase):
    def assertRaisesRegex(self, expected_exception, expected_regex, *args, **kwargs):
        if six.PY2:
            return self.assertRaisesRegexp(expected_exception, expected_regex, *args, **kwargs)
        else:
            return super(__class__, self).assertRaisesRegex(expected_exception, expected_regex, *args, **kwargs)

    def assertRegex(self, text, expected_regex, *args, **kwargs):
        if six.PY2:
            return self.assertRegexpMatches(text, expected_regex, *args, **kwargs)
        else:
            return super(__class__, self).assertRegex(text, expected_regex, *args, **kwargs)


class TestBetamax(SixTestCase):
    @property
    def cassette_name(self):
        cls = getattr(self, '__class__')
        test = self._testMethodName
        return '{0}.{1}'.format(cls.__name__, test)

    def setUp(self):
        # use self.env.set('var', 'value') and with self.env: ... to use custom envvars
        self.env = EnvironmentVarGuard()

        self.client = Client(url=TEST_URL)

        if TEST_TOKEN:
            self.client.login(token=TEST_TOKEN)

        self.recorder = Betamax(session=self.client.session)

        if TEST_RECORD_CASSETTES:
            self.recorder.use_cassette(self.cassette_name)
            self.recorder.start()
        else:
            self.recorder.config.record_mode = None

        if TEST_SCOPE_NAME:
            self.project = self.client.scope(name=TEST_SCOPE_NAME)
        elif TEST_SCOPE_ID:
            self.project = self.client.scope(id=TEST_SCOPE_ID)
        else:
            raise Exception('Cloud not retrieve the test scope, you need to provide a '
                            '`TEST_SCOPE_ID` or `TEST_SCOPE_NAME` in the `.env` file')

    def tearDown(self):
        self.recorder.stop()
        del self.env
        del self.client
