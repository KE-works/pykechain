import time

import os
import requests

from pykechain.exceptions import APIError, IllegalArgumentError
from pykechain.models import Base


class Service(Base):
    """A virtual object representing a KE-chain scope."""

    def __init__(self, json, **kwargs):
        # type: (dict, **Any) -> None
        """Construct a scope from provided json data."""
        super(Service, self).__init__(json, **kwargs)

        self.scope_id = json.get('scope', '')
        self.version = json.get('script_version', '')

    def __repr__(self):  # pragma: no cover
        return "<pyke Service '{}' id {}>".format(self.name, self.id[-8:])

    def refresh(self):
        """Refresh the Service from KE-chain."""
        fresh_service = self._client.service(pk=self.id)
        self.__dict__.update(fresh_service.__dict__)

    def execute(self, interactive=False):
        """
        Execute the service.

        For interactive (notebook) service execution, set interactive to True, defaults to False

        :param interactive: (optional) True if the notebook service should execute in interactive mode
        :return: ServiceExecution when succesfull
        """
        url = self._client._build_url('service_execute', service_id=self.id)
        r = self._client._request('GET', url, params=dict(interactive=interactive, format='json'))

        if r.status_code != requests.codes.accepted:
            raise APIError("Could not execute service '{}': {}".format(self, (r.status_code, r.json())))

        data = r.json()
        return ServiceExecution(json=data.get('results')[0], client=self._client)

    def edit(self, name=None, description=None, version=None, **kwargs):
        """Edit service details."""
        update_dict = {'id': self.id}
        if name:
            if not isinstance(name, str):
                raise IllegalArgumentError("name should be provided as a string")
            update_dict.update({'name': name})
        if description:
            if not isinstance(description, str):
                raise IllegalArgumentError("description should be provided as a string")
            update_dict.update({'description': description})
        if version:
            if not isinstance(version, str):
                raise IllegalArgumentError("description should be provided as a string")
            update_dict.update({'script_version': version})

        if kwargs:  # pragma: no cover
            update_dict.update(**kwargs)
        r = self._client._request('PUT', self._client._build_url('service', service_id=self.id), json=update_dict)

        if r.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Service ({})".format(r))

        if name:
            self.name = name
        if version:
            self.version = version

    def upload(self, pkg_path=None):
        """Upload a python script to the service."""
        if os.path.exists(pkg_path):
            self._upload(pkg_path=pkg_path)

    def _upload(self, pkg_path):
        url = self._client._build_url('service_upload', service_id=self.id)

        r = self._client._request('POST', url,
                                  files={'attachment': (os.path.basename(pkg_path), open(pkg_path, 'rb'))})

        if r.status_code != requests.codes.ok:
            raise APIError("Could not upload service script file (or kecpkg)")

    def save_as(self, target_dir=None):
        filename = self._json_data.get('script_file_name')
        full_path = os.path.join(target_dir or os.getcwd(), filename)

        url = self._client._build_url('service_download', service_id=self.id)
        response = self._client._request('GET', url)
        if response.status_code != requests.codes.ok:
            raise APIError("Could not download service script file")

        with open(full_path, 'w+b') as f:
            for chunk in response:
                f.write(chunk)

    def get_executions(self):
        return self._client.service_executions(service=self.id, scope=self.scope_id)


class ServiceExecution(Base):
    """A virtual object representing a KE-chain scope."""

    def __init__(self, json, **kwargs):
        # type: (dict, **Any) -> None
        """Construct a scope from provided json data."""
        super(ServiceExecution, self).__init__(json, **kwargs)

        self.scope_id = json.get('scope', '')
        self.status = json.get('status', '')
        self.name = json.get('service_name')

    def __repr__(self):  # pragma: no cover
        return "<pyke ServiceExecution '{}' id {}>".format(self.name, self.id[-8:])

    def refresh(self):
        """Refresh the service execution from KE-chain."""
        refreshed = self._client.service_execution(pk=self.id, _dc=str(time.time()))
        self.__dict__.update(refreshed.__dict__)

    def terminate(self):
        """
        Terminate the Service execution.

        :param silent: suppress errors, terminate silently (also when status not completed)
        :return:
        """
        url = self._client._build_url('service_execution_terminate', service_execution_id=self.id)
        r = self._client._request('GET', url, params=dict(format='json'))

        if r.status_code != requests.codes.accepted:
            raise APIError("Could not execute service '{}': {}".format(self, r.json()))

    def get_log(self, target_dir=None):
        """
        Retrieve the log of the service execution.

        :param target_dir:
        :return:
        """
        filename = 'log.txt'
        full_path = os.path.join(target_dir or os.getcwd(), filename)

        url = self._client._build_url('service_execution_log', service_execution_id=self.id)
        response = self._client._request('GET', url)
        if response.status_code != requests.codes.ok:
            raise APIError("Could not download service execution log")

        with open(full_path, 'w+b') as f:
            for chunk in response:
                f.write(chunk)

    def get_notebook_url(self):
        """
        Get the url of the notebook, if the notebook is executed in interactive mode.

        :return: full url to the interactive running notebook
        :raise: APIError when the url cannot be retrieved
        """
        url = self._client._build_url('service_execution_notebook_url', service_execution_id=self.id)
        r = self._client._request('GET', url, params=dict(format='json'))

        if r.status_code != requests.codes.ok:
            raise APIError("Could not retrieve notebook url '{}': {}".format(self, r))

        data = r.json()
        url = data.get('results')[0].get('url')
        return url
