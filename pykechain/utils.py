

def find(iterable, predicate):
    """Return the first item in the iterable that matches the predicate function."""
    return next((i for i in iterable if predicate(i)), None)
