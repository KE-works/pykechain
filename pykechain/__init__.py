"""A python library to connect and interact with KE-chain."""
import sys

from .__about__ import version
from .client import Client
from .helpers import get_project

__all__ = ("Client", "get_project", "version")

if sys.version_info.major == 2 or (
    sys.version_info.major == 3 and sys.version_info.minor < 7
):
    raise RuntimeError(
        "Python version >= `3.7` is required for this version of `pykechain` to operate. "
        "Please use `pykechain` version `3.x.x` for usage in combination with Python `3.6`"
    )
