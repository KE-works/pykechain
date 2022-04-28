import warnings

from requests import PreparedRequest, Response


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
        self.response = kwargs.pop("response", None)

        if hasattr(self.response, "request"):
            self.request = self.response.request
        else:
            self.request = kwargs.pop("request", None)

        self.msg, self.traceback, self.detail = None, None, None

        if args:
            arg = args[0]
            context = [arg if isinstance(arg, str) else arg.__repr__()]
        else:
            context = [
                "Error in request to the server."
            ]  # Default message if `APIError()`, without inputs,  is used.

        import json

        if self.response is not None and isinstance(self.response, Response):
            try:
                response_json = self.response.json()
            except json.decoder.JSONDecodeError:
                response_json = None

            if response_json:
                self.msg = response_json.get("msg")
                self.traceback = response_json.get(
                    "traceback", "provided no traceback."
                )
                self.detail = response_json.get("detail")
                self.results = response_json.get("results")
            else:
                self.traceback = self.response.text
                self.msg = self.traceback.split(r"\n"[-1])
                self.detail = None
                self.results = None

            context.extend(
                [
                    f"Server {self.traceback}",
                    f"Results:\n{json.dumps(self.results, indent=4)}",
                    f"Detail: {self.detail}",
                    f"Elapsed: {self.response.elapsed}",
                ]
            )

        if self.request is not None and isinstance(self.request, PreparedRequest):
            context.extend(
                [
                    f"Request URL: {self.request.url}",
                    f"Request method: {self.request.method}",
                ]
            )
            if self.request.body:
                try:
                    decoded_body = self.request.body.decode(
                        "UTF-8"
                    )  # Convert byte-string to string
                except AttributeError:
                    decoded_body = (
                        self.request.body
                    )  # strings (e.g. from testing cassettes) cant be decoded
                try:
                    body = json.loads(
                        decoded_body
                    )  # Convert string to Python object(s)
                except json.decoder.JSONDecodeError:
                    body = decoded_body.split("&")  # parameters in URL
                context.append(
                    f"Request data:\n{json.dumps(body, indent=4)}"
                )  # pretty printing of a json

        message = "\n".join(context)
        new_args = [message]

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


class PDFDownloadTimeoutError(APIError):
    """Error downloading the PDF because of a timeouterror."""

    pass


class _DeprecationMixin:
    __notified = False

    def __new__(cls, *args, **kwargs):
        if not cls.__notified:
            warnings.warn(
                f"`{cls.__name__}` is a wrapping class for `{str(cls.__name__)[:-1]}`. "
                f"`{cls.__name__}` will be deprecated in July 2022.",
                PendingDeprecationWarning,
            )
            cls.__notified = True

        return super().__new__(cls)
