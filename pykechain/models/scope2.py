from typing import Any  # noqa: F401

import requests

from pykechain.exceptions import APIError, NotFoundError
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

    def _update_scope_project_team(self, select_action, user, user_type):
        """
        Update the Project Team of the Scope. Updates include addition or removing of managers or members.

        :param select_action: type of action to be applied
        :type select_action: basestring
        :param user: the username of the user to which the action applies to
        :type user: basestring
        :param user_type: the type of the user (member or manager)
        :type user_type: basestring
        :raises APIError: When unable to update the scope project team.
        """
        if isinstance(user, str):
            users = self._client._retrieve_users()
            user_object = next((item for item in users['results'] if item["username"] == user), None)
            if user_object:
                url = self._client._build_url('scope2_{}'.format(select_action), scope_id=self.id)
                r = self._client._request('PUT', url,
                                          data={'user_id': user_object['pk']})
                if r.status_code != requests.codes.ok:  # pragma: no cover
                    raise APIError("Could not {} {} in Scope".format(select_action.split('_')[0], user_type))
            else:
                raise NotFoundError("User {} does not exist".format(user))
        else:
            raise TypeError("User {} should be defined as a string".format(user))

    def _edit(self, update_dict):
        url = self._client._build_url('scope2', scope_id=self.id)

        r = self._client._request('PUT', url, json=update_dict)

        if r.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Scope ({})".format(r))
        else:
            self._json_data = r.json().get('results') and r.json().get('results')[0]
