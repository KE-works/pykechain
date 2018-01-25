import os
from envparse import env

from pykechain.client import Client
from pykechain.enums import KechainEnv as kecenv, ScopeStatus
from pykechain.exceptions import ClientError


def get_project(url=None, username=None, password=None, token=None, scope=None, scope_id=None,
                env_filename=None, status=ScopeStatus.ACTIVE):
    """
    Retrieve and return the KE-chain project to be used throughout an app.

    This helper is made to bootstrap a pykechain enabled python script or an jupyter notebook with the correct
    project (technically this is a `pykechain.models.Scope` model).

    When no parameters are passed in this function, it will try to retrieve `url`, `token`, `scope` (or `scope_id`)
    from the environment variables or a neatly placed '.env' file.

    when the environment variable KECHAIN_FORCE_ENV_USE is set to true, (or ok, on, 1, yes) then the use of
    environmentvariables for the retrieval of the scope are enforced. The following environment variables can be set::

        KECHAIN_URL           - full url of KE-chain where to connect to eg: 'https://<some>.ke-chain.com'
        KECHAIN_TOKEN         - authentication token for the KE-chain user provided from KE-chain user account control
        KECHAIN_USERNAME      - the username for the credentials
        KECHAIN_PASSWORD      - the password for the credentials
        KECHAIN_SCOPE         - the name of the project / scope. Should be unique, otherwise use scope_id
        KECHAIN_SCOPE_ID      - the UUID of the project / scope.
        KECHAIN_FORCE_ENV_USE - set to 'true', '1', 'ok', or 'yes' to always use the environment variables.
        KECHAIN_SCOPE_STATUS  - the status of the Scope to retrieve, defaults to None to retrieve all scopes

    .. versionadded:: 1.12

    :param url: (optional) url of KE-chain
    :type url: basestring or None
    :param username: (optional) username for authentication (together with password, if not token)
    :type username: basestring or None
    :param password: (optional) password for username/password authentication (together with username, if not token)
    :type password: basestring or None
    :param token: (optional) token for authentication (if not username/password)
    :type token: basestring or None
    :param scope: (optional) name of the scope to retrieve from KE-chain.
    :type scope: basestring or None
    :param scope_id: (optional) UUID of the scope to retrieve and return from KE-chain
    :type scope_id: basestring or None
    :param env_filename: (optional) name of the environment filename to bootstrap the Client
    :type env_filename: basestring or None
    :param status: (optional) status of the scope to retrieve, defaults to :attr:`enums.Scopestatus.ACTIVE`
    :type status: basestring or None
    :return: pykechain.models.Scope
    :raises NotFoundError: If the scope could not be found
    :raises ClientError: If the client connection to KE-chain was unsuccessful
    :raises APIError: If other Errors occur to retrieve the scope

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
    if env.bool(kecenv.KECHAIN_FORCE_ENV_USE, default=False):
        if not os.getenv(kecenv.KECHAIN_URL):
            raise ClientError(
                "Error: KECHAIN_URL should be provided as environment variable (use of env vars is enforced)")
        if not (os.getenv(kecenv.KECHAIN_TOKEN) or
                (os.getenv(kecenv.KECHAIN_PASSWORD) and os.getenv(kecenv.KECHAIN_PASSWORD))):
            raise ClientError("Error: KECHAIN_TOKEN or KECHAIN_USERNAME and KECHAIN_PASSWORD should be provided as "
                              "environment variable(s) (use of env vars is enforced)")
        if not (os.getenv(kecenv.KECHAIN_SCOPE) or os.getenv(kecenv.KECHAIN_SCOPE_ID)):
            raise ClientError("Error: KECHAIN_SCOPE or KECHAIN_SCOPE_ID should be provided as environment variable "
                              "(use of env vars is enforced)")

    if env.bool(kecenv.KECHAIN_FORCE_ENV_USE, default=False) or \
            not any((url, username, password, token, scope, scope_id)):
        client = Client.from_env(env_filename=env_filename)
        scope_id = env(kecenv.KECHAIN_SCOPE_ID, default=None)
        scope = env(kecenv.KECHAIN_SCOPE, default=None)
        status = env(kecenv.KECHAIN_SCOPE_STATUS, default=None)
    elif (url and ((username and password) or (token)) and (scope or scope_id)) and \
            not env.bool(kecenv.KECHAIN_FORCE_ENV_USE, default=False):
        client = Client(url=url)
        client.login(username=username, password=password, token=token)
    else:
        raise ClientError("Error: insufficient arguments to connect to KE-chain. "
                          "See documentation of `pykechain.get_project()`")

    if scope_id:
        return client.scope(pk=scope_id, status=status)
    else:
        return client.scope(name=scope, status=status)
