import warnings
from requests import Response, PreparedRequest


class APIError(Exception):
    """A general KE-chain API Error occurred.

    A end-user descriptive message is required.

    :ivar response: response object
    :ivar request: request object that preceedes the response
    :ivar msg: error message in the response
    :ivar traceback: traceback in the response (from the KE-chain server)
    :ivar detail: details of the error
    """

    def __init__(self, *args, **kwargs):
        """Initialise the `APIError` with `response`, `request`, `msg`, `traceback` and `detail`.

        :param response:
        :param kwargs:
        """
        self.response = kwargs.pop('response', None)

        try:
            self.request = self.response.request
        except AttributeError:
            self.request = kwargs.pop('request', None)

        self.msg, self.traceback, self.detail = None, None, None

        context = [args[0]] if args else []

        if self.response is not None and isinstance(self.response, Response):
            response_json = self.response.json()
            # may be a KE-chain API response error
            if response_json:
                self.msg = response_json.get('msg')
                self.traceback = response_json.get('traceback', 'provided no traceback.')
                self.detail = response_json.get('detail')
            else:
                self.traceback = self.response.text
                self.msg = self.traceback.split(r'\n'[-1])

            context.extend([
                'Server {}'.format(self.traceback),
                'Elapsed: {}'.format(self.response.elapsed),
            ])

        if self.request is not None and isinstance(self.request, PreparedRequest) and self.request.body:
            import ast
            import json
            body = ast.literal_eval(self.request.body.decode("UTF-8"))  # Convert byte-string to Python list or dict

            context.extend([
                'Request URL: {}'.format(self.request.url),
                'Request method: {}'.format(self.request.method),
                'Request JSON:\n{}'.format(json.dumps(body, indent=4)),  # pretty printing of a json
            ])

        new_args = list(args) if args else ['']
        new_args[0] = '\n\n'.join(context)

        super().__init__(*new_args)


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
