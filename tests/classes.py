import collections
import datetime
import os
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
    config.default_cassette_options["match_requests_on"] = [
        "method",
        "uri",
    ]
    config.define_cassette_placeholder("<API_URL>", TEST_URL)
    config.define_cassette_placeholder("<AUTH_TOKEN>", TEST_TOKEN)
    config.define_cassette_placeholder(
        "<STORED_FILE_CDN_URL>", "https://ams3.digitaloceanspaces.com"
    )


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


#
# This is EnvironmentVarGuard implementation of python 3.
# see: https://github.com/python/cpython/blob/3.10/Lib/test/support/os_helper.py#L562
#
class EnvironmentVarGuard(collections.abc.MutableMapping):
    """Class to help protect the environment variable properly.

    Can be used as a context manager."""

    def __init__(self):
        self._environ = os.environ
        self._changed = {}

    def __getitem__(self, envvar):
        return self._environ[envvar]

    def __setitem__(self, envvar, value):
        # Remember the initial value on the first access
        if envvar not in self._changed:
            self._changed[envvar] = self._environ.get(envvar)
        self._environ[envvar] = value

    def __delitem__(self, envvar):
        # Remember the initial value on the first access
        if envvar not in self._changed:
            self._changed[envvar] = self._environ.get(envvar)
        if envvar in self._environ:
            del self._environ[envvar]

    def keys(self):
        return self._environ.keys()

    def __iter__(self):
        return iter(self._environ)

    def __len__(self):
        return len(self._environ)

    def set(self, envvar, value):
        self[envvar] = value

    def unset(self, envvar):
        del self[envvar]

    def copy(self):
        # We do what os.environ.copy() does.
        return dict(self)

    def __enter__(self):
        return self

    def __exit__(self, *ignore_exc):
        for (k, v) in self._changed.items():
            if v is None:
                if k in self._environ:
                    del self._environ[k]
            else:
                self._environ[k] = v
        os.environ = self._environ
