from unittest import TestCase, skipIf

import six
import warnings

from tests.utils import TEST_FLAG_IS_WIM2

if six.PY2:
    from test.test_support import EnvironmentVarGuard
elif six.PY3:
    from test.support import EnvironmentVarGuard

from pykechain.client import Client
from pykechain.exceptions import ForbiddenError, ClientError, NotFoundError, IllegalArgumentError
from tests.classes import TestBetamax


class TestClient(TestCase):
    def setUp(self):
        self.env = EnvironmentVarGuard()

    def test_init_default_url(self):
        client = Client()

        self.assertEqual(client.api_root, 'http://localhost:8000/')

    def test_init_custom_url(self):
        client = Client(url='http://testing.com:1234')

        self.assertEqual(client.api_root, 'http://testing.com:1234')

    def test_init_no_login(self):
        client = Client()

        self.assertNotIn('Authorization', client.headers)
        self.assertIsNone(client.auth)

    def test_init_basic_auth(self):
        client = Client()

        client.login('someuser', 'withpass')

        self.assertNotIn('Authorization', client.headers)
        self.assertTrue(client.auth)

    def test_init_token(self):
        client = Client()
        PSEUDO_TOKEN = '123123'

        client.login(token=PSEUDO_TOKEN)

        self.assertTrue(client.headers['Authorization'], 'Token {}'.format(PSEUDO_TOKEN))
        self.assertIsNone(client.auth)

    def test_init_no_ssl(self):
        client = Client(check_certificates=False)

        self.assertFalse(client.session.verify)

    # 1.12
    def test_client_raises_error_with_false_url(self):
        with self.assertRaises(ClientError):
            Client(url='wrongurl')

    def test_client_from_env(self):
        """
        Test if the client does not provide a warning when no env file can be found

            Userwarning: 'Could not any envfile.'
            '.../lib/python3.5/site-packages/envparse.py'
        """
        self.env.set('KECHAIN_URL', 'http://localhost:8000')
        with self.env:
            with warnings.catch_warnings(record=True) as captured_warnings:
                client = Client.from_env()
                self.assertEqual(len(captured_warnings), 0)


class TestClientLive(TestBetamax):
    def test_login(self):
        self.assertTrue(self.project.parts())

    def test_no_login(self):
        self.client.login('wrong', 'user')

        with self.assertRaises(ForbiddenError):
            self.client.parts()


@skipIf(not TEST_FLAG_IS_WIM2, reason="This tests is designed for WIM version 2, expected to fail on older WIM")
class TestClientAppVersions(TestBetamax):
    def test_retrieve_versions(self):
        """Test to retrieve the app versions from KE-chain"""
        app_versions = self.project._client.app_versions
        self.assertTrue(isinstance(app_versions, list))
        self.assertTrue(isinstance(app_versions[0], dict))
        self.assertTrue(set(app_versions[0].keys()),
                        {'app', 'label', 'version', 'major', 'minor', 'patch', 'prerelease'})

    def test_compare_versions(self):
        """Multitest to check all the matchings versions"""

        self.assertTrue(self.client.match_app_version(app='kechain2.core.wim', version='>=1.0.0'))
        self.assertTrue(self.client.match_app_version(label='wim', version='>=1.0.0'))
        self.assertFalse(self.client.match_app_version(label='wim', version='==0.0.1'))

        # value error
        # wrong version string (no semver string) to check against
        with self.assertRaises(ValueError):
            self.client.match_app_version(app='kechain2.core.wim', version='1.0')

        # right version, no operand in version
        with self.assertRaises(ValueError):
            self.client.match_app_version(app='kechain2.core.wim', version='1.0.0')

        # wrong operand (should be ==)
        with self.assertRaises(ValueError):
            self.client.match_app_version(app='kechain2.core.wim', version='=1.0.0')

        # not found a match version
        with self.assertRaises(IllegalArgumentError):
            self.client.match_app_version(app='kechain2.core.wim', version='')

        # no version found on the app kechain2.metrics
        with self.assertRaises(NotFoundError):
            self.client.match_app_version(app='kechain2.metrics', version='>0.0.0', default=None)

        # no version found on the app kechain2.metrics, default = True, returns True
        self.assertTrue(self.client.match_app_version(app='kechain2.metrics', version='>0.0.0', default=True))

        # no version found on the app kechain2.metrics, default = False, returns False
        self.assertFalse(self.client.match_app_version(app='kechain2.metrics', version='>0.0.0', default=False))

        # no version found on the app kechain2.metrics, default = False, returns False
        # default is set to return False in the method
        self.assertFalse(self.client.match_app_version(app='kechain2.metrics', version='>0.0.0'))

        # did not find the app
        with self.assertRaises(NotFoundError):
            self.client.match_app_version(app='nonexistingapp', version='>0.0.0', default=None)

        # did not find the app, but the default returns a False
        self.assertFalse(self.client.match_app_version(app='nonexistingapp', version='>0.0.0', default=False))

        # did not find the app, but the default returns a False, without providing the default, as the default is False
        self.assertFalse(self.client.match_app_version(app='nonexistingapp', version='>0.0.0'))
