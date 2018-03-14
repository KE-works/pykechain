import os
import requests

from pykechain.exceptions import APIError, IllegalArgumentError
from pykechain.models.base import Base


class Service(Base):
    """
    A virtual object representing a KE-chain Service.

    .. versionadded:: 1.13
    """

    def __init__(self, json, **kwargs):
        """Construct a scope from provided json data."""
        super(Service, self).__init__(json, **kwargs)

        self.scope_id = json.get('scope', '')
        self.version = json.get('script_version', '')

    def __repr__(self):  # pragma: no cover
        return "<pyke Service '{}' id {}>".format(self.name, self.id[-8:])

    def execute(self, interactive=False):
        """
        Execute the service.

        For interactive (notebook) service execution, set interactive to True, defaults to False.

        .. versionadded:: 1.13

        :param interactive: (optional) True if the notebook service should execute in interactive mode.
        :type interactive: bool or None
        :return: ServiceExecution when successful.
        :raises APIError: when unable to execute
        """
        url = self._client._build_url('service_execute', service_id=self.id)
        response = self._client._request('GET', url, params=dict(interactive=interactive, format='json'))

        if response.status_code != requests.codes.accepted:  # pragma: no cover
            raise APIError("Could not execute service '{}': {}".format(self, (response.status_code, response.json())))

        data = response.json()
        return ServiceExecution(json=data.get('results')[0], client=self._client)

    def edit(self, name=None, description=None, version=None, **kwargs):
        """
        Edit Service details.

        .. versionadded:: 1.13

        :param name: (optional) name of the service to change.
        :type name: basestring or None
        :param description: (optional) description of the service.
        :type description: basestring or None
        :param version: (optional) version number of the service.
        :type version: basestring or None
        :param kwargs: (optional) additional keyword arguments to change.
        :type kwargs: dict or None
        :raises IllegalArgumentError: when you provide an illegal argument.
        :raises APIError: if the service could not be updated.
        """
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
        response = self._client._request('PUT',
                                         self._client._build_url('service', service_id=self.id), json=update_dict)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Service ({})".format(response))

        if name:
            self.name = name
        if version:
            self.version = version

    def delete(self):
        # type: () -> None
        """Delete this service.

        :raises APIError: if delete was not succesfull.
        """
        response = self._client._request('DELETE', self._client._build_url('service', service_id=self.id))

        if response.status_code != requests.codes.no_content:  # pragma: no cover
            raise APIError("Could not delete service: {} with id {}".format(self.name, self.id))

    def upload(self, pkg_path):
        """
        Upload a python script (or kecpkg) to the service.

        .. versionadded:: 1.13

        :param pkg_path: path to the python script or kecpkg to upload.
        :type pkg_path: basestring
        :raises APIError: if the python package could not be uploaded.
        :raises OSError: if the python package could not be located on disk.
        """
        if os.path.exists(pkg_path):
            self._upload(pkg_path=pkg_path)
        else:
            raise OSError("Could not locate python package to upload in '{}'".format(pkg_path))

    def _upload(self, pkg_path):
        url = self._client._build_url('service_upload', service_id=self.id)

        response = self._client._request('POST', url,
                                         files={'attachment': (os.path.basename(pkg_path), open(pkg_path, 'rb'))})

        if response.status_code != requests.codes.accepted:  # pragma: no cover
            raise APIError("Could not upload service script file (or kecpkg) ({})".format(response))

    def save_as(self, target_dir=None):
        """
        Save the kecpkg service script to an (optional) target dir.

        Retains the filename of the service as known in KE-chain.

        .. versionadded:: 1.13

        :param target_dir: (optional) target dir. If not provided will save to current working directory.
        :type target_dir: basestring or None
        :raises APIError: if unable to download the service.
        :raises OSError: if unable to save the service kecpkg file to disk.
        """
        filename = self._json_data.get('script_file_name')
        full_path = os.path.join(target_dir or os.getcwd(), filename)

        url = self._client._build_url('service_download', service_id=self.id)
        response = self._client._request('GET', url)
        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not download service script file ({})".format(response))

        with open(full_path, 'w+b') as f:
            for chunk in response:
                f.write(chunk)

    def get_executions(self, **kwargs):
        """
        Retrieve the executions related to the current service.

        .. versionadded:: 1.13

        :param kwargs: (optional) additional search keyword arguments to limit the search even further.
        :type kwargs: dict
        :return: list of ServiceExecutions associated to the current service.
        """
        return self._client.service_executions(service=self.id, scope=self.scope_id, **kwargs)


class ServiceExecution(Base):
    """
    A virtual object representing a KE-chain Service Execution.

    .. versionadded:: 1.13
    """

    def __init__(self, json, **kwargs):
        """Construct a scope from provided json data."""
        super(ServiceExecution, self).__init__(json, **kwargs)

        self.scope_id = json.get('scope', '')
        self.status = json.get('status', '')
        self.name = json.get('service_name')

    def __repr__(self):  # pragma: no cover
        return "<pyke ServiceExecution '{}' id {}>".format(self.name, self.id[-8:])

    def terminate(self):
        """
        Terminate the Service execution.

        .. versionadded:: 1.13

        :return: None if the termination request was successful
        :raises APIError: When the service execution could not be terminated.
        """
        url = self._client._build_url('service_execution_terminate', service_execution_id=self.id)
        response = self._client._request('GET', url, params=dict(format='json'))

        if response.status_code != requests.codes.accepted:  # pragma: no cover
            raise APIError("Could not execute service '{}': {}".format(self, response))

    def get_log(self, target_dir=None, log_filename='log.txt'):
        """
        Retrieve the log of the service execution.

        .. versionadded:: 1.13

        :param target_dir: (optional) directory path name where the store the log.txt to.
        :type target_dir: basestring or None
        :param log_filename: (optional) log filename to write the log to, defaults to `log.txt`.
        :type log_filename: basestring or None
        :raises APIError: if the logfile could not be found.
        :raises OSError: if the file could not be written.
        """
        full_path = os.path.join(target_dir or os.getcwd(), log_filename)

        url = self._client._build_url('service_execution_log', service_execution_id=self.id)
        response = self._client._request('GET', url)
        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not download service execution log")

        with open(full_path, 'w+b') as f:
            for chunk in response:
                f.write(chunk)

    def get_notebook_url(self):
        """
        Get the url of the notebook, if the notebook is executed in interactive mode.

        .. versionadded:: 1.13

        :return: full url to the interactive running notebook as `basestring`
        :raises APIError: when the url cannot be retrieved.
        """
        url = self._client._build_url('service_execution_notebook_url', service_execution_id=self.id)
        response = self._client._request('GET', url, params=dict(format='json'))

        if response.status_code != requests.codes.ok:
            raise APIError("Could not retrieve notebook url '{}': {}".format(self, response))

        data = response.json()
        url = data.get('results')[0].get('url')
        return url
