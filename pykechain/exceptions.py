class APIError(Exception):
    """A general API Error.

    A end-user descriptive message is required
    """

    pass


class ForbiddenError(APIError):
    """A login is required."""

    pass


class MultipleFoundError(APIError):
    """Multiple objects are found, while a single object is requested."""

    pass


class NotFoundError(APIError):
    """Object not found error."""

    pass


class ClientError(APIError):
    """Error with instantiating the Client."""

    pass


class IllegalArgumentError(ValueError):
    """Error when provided illegal arguments to a function or method."""

    pass


class InspectorComponentError(Exception):
    """Error in the InspectorComponent."""

    pass
