from unittest import TestCase

from requests import PreparedRequest

from pykechain.exceptions import (
    APIError, ForbiddenError, MultipleFoundError, NotFoundError, ClientError, IllegalArgumentError,
    InspectorComponentError)
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

    def test_api_error_with_objects(self):
        APIError(['text in a list'])
        APIError(('text in a tuple',))
        APIError(dict(text='in a dict'))

    def test_inheritance(self):
        self.assertTrue(issubclass(APIError, BaseException))
        self.assertTrue(issubclass(ForbiddenError, APIError))
        self.assertTrue(issubclass(MultipleFoundError, APIError))
        self.assertTrue(issubclass(NotFoundError, APIError))
        self.assertTrue(issubclass(ClientError, APIError))

        self.assertFalse(issubclass(IllegalArgumentError, APIError))
        self.assertFalse(issubclass(InspectorComponentError, APIError))

    def test_creation(self):
        for test_class in [
            APIError,
            ForbiddenError,
            MultipleFoundError,
            NotFoundError,
            ClientError,
            IllegalArgumentError,
            InspectorComponentError,
        ]:
            with self.subTest(msg=test_class.__name__):
                test_class()


class TestExceptionsLive(TestBetamax):

    def setUp(self):
        super().setUp()
        url = self.client._build_url('activities')
        self.response = self.client._request(method='GET', url=url, params={'limit': 1})

    def test_api_error_with_response(self):
        api_error = APIError(response=self.response)

        # testing
        self.assertIsInstance(api_error.request, PreparedRequest)
        self.assertEqual(self.response, api_error.response)
        with self.assertRaises(APIError):
            raise api_error

    def test_api_error_with_argument_and_response(self):
        APIError(dict(text='my dict'), response=self.response)
