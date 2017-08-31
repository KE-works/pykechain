"""A python library to connect and interact with KE-chain."""

from .__about__ import version
from .client import Client

__all__ = (
    'Client', 'version'
)
