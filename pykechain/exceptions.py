
class APIError(Exception):
    """
    A general API Error

    A end-user descriptive message is required
    """
    pass


class LoginRequiredError(APIError):
    """
    A login is required
    """
    pass


class MultipleFoundError(APIError):
    """
    Multiple objects are found, while a single object is requested
    """
    pass


class NotFoundError(APIError):
    """
    Object not found error
    """
    pass
