import datetime
import os
from test.support import EnvironmentVarGuard
from unittest import TestCase

import pytz
from betamax import Betamax

from pykechain import Client
from tests.utils import (
    TEST_RECORD_CASSETTES,
    TEST_SCOPE_ID,
    TEST_SCOPE_NAME,
    TEST_TOKEN,
    TEST_URL,
)

with Betamax.configure() as config:
    config.cassette_library_dir = os.path.join(os.path.dirname(__file__), "cassettes")
    config.define_cassette_placeholder("<API_URL>", TEST_URL)
    config.define_cassette_placeholder("<AUTH_TOKEN>", TEST_TOKEN)


class TestBetamax(TestCase):
    time = datetime.datetime(year=2020, month=1, day=1, tzinfo=pytz.UTC)

    @property
    def cassette_name(self):
        test = self._testMethodName
        return f"{self.__class__.__name__}.{test}"

    def setUp(self):
        # use self.env.set('var', 'value') and with self.env: ... to use custom environmental variables
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
            raise Exception(
                "Could not retrieve the test scope, you need to provide a "
                "`TEST_SCOPE_ID` or `TEST_SCOPE_NAME` in your `.env` file"
            )

    def tearDown(self):
        self.recorder.stop()
        del self.env
        del self.client
