

class LoginRequiredError(Exception):
    """
    A login is required
    """
    pass

class MultipleFoundError(Exception):
    """
    Multiple objects are found, while a single object is requested
    """
    pass

class NotFoundError(Exception):
    """
    Object not found error
    """
    pass
