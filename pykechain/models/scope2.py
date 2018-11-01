from typing import Any  # noqa: F401

from pykechain.models import Scope


class Scope2(Scope):
    """A virtual object representing a KE-chain scope."""

    def __init__(self, json, **kwargs):
        # type: (dict, **Any) -> None
        """Construct a scope from provided json data."""
        super(Scope, self).__init__(json, **kwargs)

        # for 'kechain2.core.wim <2.0.0'
        self.process = json.get('process')
        # for 'kechain2.core.wim >=2.0.0'
        self.workflow_root = json.get('workflow_root_id')

    @property
    def bucket(self):
        """Bucket of the scope is deprecated in version 2."""
        raise DeprecationWarning("Bucket has been deprecated in scope version 2")
