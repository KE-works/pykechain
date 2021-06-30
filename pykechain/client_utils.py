from ssl import SSLError

from urllib3 import Retry
from urllib3.exceptions import MaxRetryError


class PykeRetry(Retry):
    """
    Pykechain Implementation of urllib3.Retry function.

    It contains a fast bailout of any SSLCertificate Errors.
    """

    def increment(
        self,
        method=None,
        url=None,
        response=None,
        error=None,
        _pool=None,
        _stacktrace=None,
    ):
        """In case of failed verification of self signed certificate we short circuit the retry routine."""
        if self._is_ssl_error(error):
            raise MaxRetryError(_pool, url, error)

        return super().increment(
            method=method,
            url=url,
            response=response,
            error=error,
            _pool=_pool,
            _stacktrace=_stacktrace,
        )

    def _is_ssl_error(self, error):
        return error and isinstance(error, SSLError)
