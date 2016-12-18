

def find(iterable, predicate):
    return next((i for i in iterable if predicate(i)), None)
