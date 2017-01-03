from pykechain.client import Client
from pykechain.exceptions import LoginRequiredError
from tests.classes import TestBetamax


class TestClient(object):

    def test_init_default_url(self):
        client = Client()

        assert client.api_root == 'http://localhost:8000/'

    def test_init_custom_url(self):
        client = Client(url='http://testing.com:1234')

        assert client.api_root == 'http://testing.com:1234'

    def test_init_no_login(self):
        client = Client()

        assert 'Authorization' not in client.headers
        assert client.auth is None

    def test_init_basic_auth(self):
        client = Client()

        client.login('admin', 'pass')

        assert 'Authorization' not in client.headers
        assert client.auth

    def test_init_token(self):
        client = Client()

        client.login(token='123123')

        assert client.headers['Authorization'] == 'Token 123123'
        assert client.auth is None

    def test_init_no_ssl(self):
        client = Client(check_certificates=False)

        assert client.session.verify is False


class TestClientLive(TestBetamax):

    def test_login(self):
        assert self.client.parts()

    def test_no_login(self):
        self.client.login('wrong', 'user')

        with self.assertRaises(LoginRequiredError):
            self.client.parts()