from ssl import SSLCertVerificationError

from urllib3 import Retry
from urllib3.exceptions import MaxRetryError


class PykeRetry(Retry):
    def increment(
        self,
        method=None,
        url=None,
        response=None,
        error=None,
        _pool=None,
        _stacktrace=None,
    ):
        """
        In case of failed verification of self signed certificate we short circuit the retry routine.
        """
        if self._is_self_signed_certificate_error(error):
            raise MaxRetryError(_pool, url, error)

        return super().increment(
            method=method,
            url=url,
            response=response,
            error=error,
            _pool=_pool,
            _stacktrace=_stacktrace,
        )

    def _is_self_signed_certificate_error(self, error):
        error_msg = "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self signed certificate"
        return error and isinstance(error, SSLCertVerificationError) and error_msg in str(error)
