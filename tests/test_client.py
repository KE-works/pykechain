from unittest import TestCase

import six
import warnings

if six.PY2:
    from test.test_support import EnvironmentVarGuard
elif six.PY3:
    from test.support import EnvironmentVarGuard

from pykechain.client import Client
from pykechain.exceptions import ForbiddenError, ClientError
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
        self.assertTrue(self.client.parts())

    def test_no_login(self):
        self.client.login('wrong', 'user')

        with self.assertRaises(ForbiddenError):
            self.client.parts()
