"""A python library to connect and interact with KE-chain."""
import sys

import six

from .__about__ import version
from .client import Client
from .helpers import get_project

__all__ = (
    'Client', 'get_project', 'version'
)

if six.PY2 or (sys.version_info.major == 3 and sys.version_info.minor <= 4):
    raise RuntimeError("Python version >= `3.5` is required for this version of `pykechain` to operate. "
                       "Please use `pykechain` version < `3.0` for usage in combination with Python `2.7`")
