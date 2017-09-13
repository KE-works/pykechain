from envparse import env

from pykechain.client import Client
from pykechain.exceptions import ClientError


def get_project(url=None, username=None, password=None, token=None, scope=None, scope_id=None,
                env_filename=None):
    """
    Retrieve and return the KE-chain project to be used throughout an app.

    This helper is made to bootstrap a pykechain enabled python script or an jupyter notebook with the correct
    project (technically this is a `pykechain.models.Scope` model).

    When no parameters are passed in this function, it will try to retrieve `url`, `token`, `scope` (or `scope_id`)
    from the environment variables or a neatly placed '.env' file.

    :param url: (optional) url of KE-chain
    :param username: (optional) username for authentication (together with password, if not token)
    :param password: (optional) password for username/password authentication (together with username, if not token)
    :param token: (optional) token for authentication (if not username/password)
    :param scope: (optional) name of the scope to retrieve from KE-chain.
    :param scope_id: (optional) UUID of the scope to retrieve and return from KE-chain
    :param env_filename: (optional) name of the environment filename to bootstrap the Client
    :return: pykechain.models.Scope
    :raises: NotFoundError, ClientError, APIError

    Example
    -------
    An example with parameters provided

    >>> from pykechain import get_project
    >>> project = get_project(url='http://localhost:8000',
    ...     username='foo', password='bar', scope='1st!')
    >>> print(project.name)
    1st

    An example with a .env file on disk::

        # This is an .env file on disk.
        KECHAIN_TOKEN=bd9377793f7e74a29dbb11fce969
        KECHAIN_URL=http://localhost:8080
        KECHAIN_SCOPE_ID=c9f0-228e-4d3a-9dc0-ec5a75d7

    >>> project = get_project(env_filename='/path/to/.env')
    >>> project.id
    c9f0-228e-4d3a-9dc0-ec5a75d7

    An example for get_project that will extract all from the environment variables

    >>> env_vars = os.environ
    >>> env_vars.get('KECHAIN_TOKEN')
    bd9377793f7e74a29dbb11fce969
    >>> env_vars.get('KECHAIN_URL')
    http://localhost:8080
    >>> env_vars.get('KECHAIN_SCOPE')
    Bike Project
    >>> project = get_project()
    >>> project.name
    Bike Project
    """
    if not any((url, username, password, token, scope, scope_id)):
        client = Client.from_env(env_filename=env_filename)
        scope_id = env('KECHAIN_SCOPE_ID', default=None)
        scope = env('KECHAIN_SCOPE', default=None)
    elif (url and ((username and password) or (token)) and (scope or scope_id)):
        client = Client(url=url)
        client.login(username=username, password=password, token=token)
    else:
        raise ClientError("Error: insufficient arguments to connect to KE-chain. "
                          "See documentation of `pykechain.get_project()`")

    if scope_id:
        return client.scope(pk=scope_id)
    else:
        return client.scope(name=scope)
