from unittest import TestCase

from requests import PreparedRequest

from pykechain.exceptions import APIError
from tests.classes import TestBetamax


class TestExceptions(TestCase):

    def test_api_error(self):
        api_error = APIError()

        with self.assertRaises(Exception):
            raise api_error

    def test_api_error_with_message(self):
        api_error = APIError('This is the error message.')

        with self.assertRaises(APIError):
            raise api_error


class TestExceptionsLive(TestBetamax):

    def test_api_error_with_response(self):
        # setUp
        url = self.client._build_url('activities')
        response = self.client._request(method='GET', url=url)
        api_error = APIError(response=response)

        # testing
        self.assertIsInstance(api_error.request, PreparedRequest)
        self.assertEqual(response, api_error.response)
        with self.assertRaises(APIError):
            raise api_error
