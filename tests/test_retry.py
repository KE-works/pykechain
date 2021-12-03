from ssl import SSLError

from unittest import TestCase

from pykechain.client_utils import PykeRetry
from pykechain.defaults import (
    RETRY_BACKOFF_FACTOR,
    RETRY_ON_CONNECTION_ERRORS,
    RETRY_ON_READ_ERRORS,
    RETRY_ON_REDIRECT_ERRORS,
    RETRY_TOTAL,
)
from urllib3.exceptions import MaxRetryError


class TestPykeRetry(TestCase):
    def test_short_circuit_on_self_signed_cert_error(self):
        """Retry should return early if self signed cert verification fails"""
        retry = PykeRetry(
            total=RETRY_TOTAL,
            connect=RETRY_ON_CONNECTION_ERRORS,
            read=RETRY_ON_READ_ERRORS,
            redirect=RETRY_ON_REDIRECT_ERRORS,
            backoff_factor=RETRY_BACKOFF_FACTOR,
        )

        with self.assertRaises(MaxRetryError):
            retry.increment(
                error=SSLError(
                    "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self signed"
                    " certificate"
                )
            )
