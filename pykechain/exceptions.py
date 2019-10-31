from requests import Response


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
        response = kwargs.pop('response', None)
        self.response = response
        self.request = kwargs.pop('request', None)
        if (response is not None and not self.request and hasattr(response, 'request')):
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
