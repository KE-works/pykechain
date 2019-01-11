import requests
from six import text_type, string_types
from typing import Any  # noqa: F401

from pykechain.enums import Multiplicity
from pykechain.exceptions import APIError, NotFoundError, ForbiddenError
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
        """Bucket of the scope is deprecated in version 2.

        .. deprecated:: 3.0
           A `bucket` is a deprecated concept in KE-chain 3 backends. Use `scope_id` instead.
        """
        raise DeprecationWarning("Bucket has been deprecated in scope version 2")

    @property
    def team(self):
        """Team to which the scope is assigned."""
        team_dict = self._json_data.get('team_id_name')
        if team_dict and team_dict.get('id'):
            return self._client.team(pk=team_dict.get('id'))
        else:
            return None

    def refresh(self, json=None, url=None, extra_params=None):
        """Refresh the object in place."""
        from pykechain.client import API_EXTRA_PARAMS
        super(Scope2, self).refresh(json=json,
                                    url=self._client._build_url('scope2', scope_id=self.id),
                                    extra_params=API_EXTRA_PARAMS['scope2'])

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
        if isinstance(user, (string_types, text_type)):
            from pykechain.client import API_EXTRA_PARAMS
            users = self._client._retrieve_users()
            user_object = next((item for item in users['results'] if item["username"] == user), None)
            if user_object:
                url = self._client._build_url('scope2_{}'.format(select_action), scope_id=self.id)

                response = self._client._request('PUT', url,
                                                 params=API_EXTRA_PARAMS[self.__class__.__name__.lower()],
                                                 data={'user_id': user_object['pk']})
                if response.status_code != requests.codes.ok:  # pragma: no cover
                    raise APIError("Could not {} {} in Scope".format(select_action.split('_')[0], user_type))

                self._json_data = response.json().get('results')[0]
            else:
                raise NotFoundError("User {} does not exist".format(user))
        else:
            raise TypeError("User {} should be defined as a string".format(user))

    def _edit(self, update_dict):
        from pykechain.client import API_EXTRA_PARAMS
        if update_dict.get('options'):
            update_dict['scope_options'] = update_dict.get('options')
            del update_dict['options']
        if update_dict.get('team'):
            update_dict['team_id'] = update_dict.get('team')
            del update_dict['team']

        url = self._client._build_url('scope2', scope_id=self.id)

        response = self._client._request('PUT', url, params=API_EXTRA_PARAMS[self.__class__.__name__.lower()],
                                         json=update_dict)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Scope ({})".format(response))

        self.refresh(json=response.json().get('results')[0])

    def parts(self, *args, **kwargs):
        """Retrieve parts belonging to this scope.

        This uses

        See :class:`pykechain.Client.parts` for available parameters.
        """
        return self._client.parts(*args, scope_id=self.id, **kwargs)

    def part(self, *args, **kwargs):
        """Retrieve a single part belonging to this scope.

        See :class:`pykechain.Client.part` for available parameters.
        """
        return self._client.part(*args, scope_id=self.id, **kwargs)

    def properties(self, *args, **kwargs):
        """Retrieve properties belonging to this scope.

        .. versionadded: 3.0

        See :class:`pykechain.Client.properties` for available parameters.
        """
        return self._client.properties(*args, scope_id=self.id, **kwargs)

    def property(self, *args, **kwargs):
        """Retrieve a single property belonging to this scope.

        .. versionadded: 3.0

        See :class:`pykechain.Client.property` for available parameters.
        """
        return self._client.property(*args, scope_id=self.id, **kwargs)

    def model(self, *args, **kwargs):
        """Retrieve a single model belonging to this scope.

        See :class:`pykechain.Client.model` for available parameters.
        """
        return self._client.model(*args, scope_id=self.id, **kwargs)

    def create_model_with_properties(self, parent, name, multiplicity=Multiplicity.ZERO_MANY,
                                     properties_fvalues=None, **kwargs):
        """Create a model with its properties in a single API request.

        See :func:`pykechain.Client.create_model_with_properties()` for available parameters.
        """
        return self._client.create_model_with_properties(parent, name, multiplicity=multiplicity,
                                                         properties_fvalues=properties_fvalues, **kwargs)

    def clone(self, *args, **kwargs):
        """Clone a scope.

        See :method:`pykechain.Client.clone_scope()` for available paramters.
        """
        return self._client.clone_scope(source_scope=self, **kwargs)

    def delete(self):
        """Delete the scope.

        Only works with enough permissions

        .. versionadded: 3.0
        :raises ForbiddenError: if you do not have the permissions to delete a scope
        """
        url = self._client._build_url('scope2', scope_id=self.id)
        response = self._client._request('DELETE', url)

        if response.status_code != requests.codes.no_content:  # pragma: no cover
            if response.status_code == requests.codes.forbiddem:
                raise ForbiddenError("Forbidden to delete scope, {}: {}".format(str(response), response.content))
            raise APIError("Could not delete scope, {}: {}".format(str(response), response.content))





