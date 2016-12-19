from kechain2.client import Client

client = Client()


def login(*args, **kwargs):
    return client.login(*args, **kwargs)


def parts(*args, **kwargs):
    return client.parts(*args, **kwargs)


def part(*args, **kwargs):
    return client.part(*args, **kwargs)

