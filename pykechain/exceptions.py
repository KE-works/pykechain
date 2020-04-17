import warnings
from typing import Text

from requests import Response


class APIError(Exception):
    """A general KE-chain API Error occurred.

    A end-user descriptive message is required.

    :ivar response: response object
    :ivar request: request object that precedes the response
    :ivar msg: error message in the response
    :ivar traceback: traceback in the response (from the KE-chain server)
    :ivar detail: details of the error
    """

    def __init__(self, *args, **kwargs):
        """Initialise the `APIError` with `response`, `request`, `msg`, `traceback` and `detail`.

        :param response:
        :param kwargs:
        """
        response = kwargs.pop('response', None)
        self.response = response
        self.request = kwargs.pop('request', None)
        if response is not None and not self.request and hasattr(response, 'request'):
            self.request = self.response.request
        self.msg, self.traceback, self.detail = None, None, None
        super(APIError, self).__init__(*args, **kwargs)

        if isinstance(self.response, Response) and 'content' in self.response:
            # may be a KE-chain API response error
            if self.response.json():
                self.msg = self.response.json().get('msg')
                self.traceback = self.response.json().get('traceback')
                self.detail = self.response.json().get('detail')
            else:
                self.traceback = self.response.text
                self.msg = self.traceback.split(r'\n'[-1])


class ForbiddenError(APIError):
    """A login is required."""

    pass


class MultipleFoundError(APIError):
    """Multiple objects are found, while a single object is requested."""

    pass


class NotFoundError(APIError):
    """No object is found."""

    pass


class ClientError(APIError):
    """When instantiating the Client an Error occurred."""

    pass


class IllegalArgumentError(ValueError):
    """Illegal arguments where provided."""

    pass


class InspectorComponentError(Exception):
    """Error in the InspectorComponent."""

    pass


class _DeprecationMixin:

    __notified = False

    def __new__(cls, *args, **kwargs):
        if not cls.__notified:
            warnings.warn('`{n}` is a wrapping class for `{nn}`. `{n}` will be deprecated in version vX.X.X.'
                          .format(n=cls.__name__, nn=str(cls.__name__)[:-1]), PendingDeprecationWarning)
            cls.__notified = True

        return super().__new__(cls)


def api_error_traceback(message: Text, response: Response) -> APIError:
    """
    Convert the API response into an APIError with more context.

    :param message: Custom text message, e.g. "Could not update Part."
    :type message: str
    :param response: Response object from the request.
    :type response: Response
    :return: APIError object that must be raised to throw the error during runtime.
    :rtype APIError
    """
    import ast
    import json

    request = response.request
    body = ast.literal_eval(request.body.decode("UTF-8"))  # Convert byte-string to Python list or dict
    context_list = [
        message,
        'Server {}'.format(response.json().get('traceback', 'provided no traceback.')),
        'Elapsed timedelta: {}'.format(response.elapsed),
        'Request URL: {}'.format(request.url),
        'Request method: {}'.format(request.method),
        'Request JSON:\n{}'.format(json.dumps(body, indent=4)),  # pretty printing of a json
    ]
    context = '\n\n'.join(context_list)
    return APIError(context)
