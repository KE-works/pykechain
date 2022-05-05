import os
from datetime import datetime

import requests
from typing import Dict, Optional, Union

from pykechain.enums import (
    ServiceScriptUser,
    ServiceExecutionStatus,
    ServiceType,
    ServiceEnvironmentVersion,
)
from pykechain.exceptions import APIError
from pykechain.models.base import Base, BaseInScope
from pykechain.models.input_checks import check_text, check_enum, check_type
from pykechain.utils import parse_datetime, Empty, clean_empty_values, empty


class Service(BaseInScope):
    """
    A virtual object representing a KE-chain Service.

    .. versionadded:: 1.13

    :ivar id: id of the service
    :type id: uuid
    :ivar name: name of the service
    :type name: str
    :ivar description: description of the service
    :type description: str
    :ivar version: version number of the service, as provided by uploaded
    :type version: str
    :ivar type: type of the service. One of the :class:`ServiceType`
    :type type: str
    :ivar filename: filename of the service
    :type filename: str
    :ivar environment: environment in which the service will execute. One of :class:`ServiceEnvironmentVersion`
    :type environment: str
    :ivar updated_at: datetime in UTC timezone when the Service was last updated
    :type updated_at: datetime

    .. versionadded:: 3.0

    :ivar trusted: Trusted flag. If the kecpkg is trusted.
    :ivar run_as: User to run the script as. One of :class:`ServiceScriptUser`.
    :ivar verified_on: Date when the kecpkg was verified by KE-chain (if verification pipeline is enabled)
    :ivar verification_results: Results of the verification (if verification pipeline is enabled)
    """

    def __init__(self, json, **kwargs):
        """Construct a service from provided json data."""
        super().__init__(json, **kwargs)
        del self.created_at

        self.description = json.get("description", "")
        self.version = json.get("script_version", "")
        self.filename = json.get("script_file_name")
        self.type = json.get("script_type")
        self.environment = json.get("env_version")

        # for SIM3 version
        self.trusted: bool = json.get("trusted")
        self.run_as: str = json.get("run_as")
        self.verified_on: Optional[datetime] = parse_datetime(json.get("verified_on"))
        self.verification_results: Dict = json.get("verification_results")

    def __repr__(self):  # pragma: no cover
        return f"<pyke Service '{self.name}' id {self.id[-8:]}>"

    def execute(
        self, interactive: Optional[bool] = False, **kwargs
    ) -> "ServiceExecution":
        """
        Execute the service.

        For interactive (notebook) service execution, set interactive to True, defaults to False.

        .. versionadded:: 1.13

        :param interactive: (optional) True if the notebook service should execute in interactive mode.
        :type interactive: bool or None
        :return: ServiceExecution when successful.
        :raises APIError: when unable to execute
        """
        request_params = dict(
            interactive=check_type(interactive, bool, "interactive"),
            format="json",
            **kwargs,
        )

        url = self._client._build_url("service_execute", service_id=self.id)
        response = self._client._request("GET", url, params=request_params)

        if response.status_code == requests.codes.conflict:  # pragma: no cover
            raise APIError(
                f"Conflict: Could not execute Service {self} as it is already running.",
                response=response,
            )
        elif response.status_code != requests.codes.accepted:  # pragma: no cover
            raise APIError(f"Could not execute Service {self}", response=response)

        data = response.json()
        return ServiceExecution(json=data.get("results")[0], client=self._client)

    def edit(
        self,
        name: Optional[Union[str, Empty]] = empty,
        description: Optional[Union[str, Empty]] = empty,
        version: Optional[Union[str, Empty]] = empty,
        type: Optional[Union[ServiceType, Empty]] = empty,
        environment_version: Optional[Union[ServiceEnvironmentVersion, Empty]] = empty,
        run_as: Optional[Union[ServiceScriptUser, Empty]] = empty,
        trusted: Optional[Union[bool, Empty]] = empty,
        **kwargs,
    ) -> None:
        """
        Edit Service details.

        Setting an input to None will clear out the value (exception being name).

        .. versionadded:: 1.13

        :param name: (optional) name of the service to change. Cannot be cleared.
        :type name: basestring or None or Empty
        :param description: (optional) description of the service. Can be cleared.
        :type description: basestring or None or Empty
        :param version: (optional) version number of the service. Can be cleared.
        :type version: basestring or None or Empty
        :param type: (optional) script type (Python or Notebook). Cannot be cleared.
        :type type: ServiceType or None or Empty
        :param environment_version: (optional) environment version of the service. Cannot be cleared.
        :type environment_version: ServiceEnvironmentVersion or None or Empty
        :param run_as: (optional) user to run the service as. Defaults to kenode user (bound to scope).
                    Cannot be cleared.
        :type run_as: ServiceScriptUser or None or Empty
        :param trusted: (optional) flag whether the service is trusted, default if False. Cannot be cleared.
        :type trusted: bool or None or Empty
        :raises IllegalArgumentError: when you provide an illegal argument.
        :raises APIError: if the service could not be updated.

        Example
        -------
        >>> service.edit(name='Car service',version='203')

        Not mentioning an input parameter in the function will leave it unchanged. Setting a parameter as None will
        clear its value (where that is possible). The example below will clear the description and edit the name.

        >>> service.edit(name="Plane service",description=None)

        """
        update_dict = {
            "id": self.id,
            "name": check_text(name, "name") or self.name,
            "description": check_text(description, "description") or "",
            "trusted": check_type(trusted, bool, "trusted") or self.trusted,
            "script_type": check_enum(type, ServiceType, "type") or self.type,
            "env_version": check_enum(
                environment_version, ServiceEnvironmentVersion, "environment version"
            )
            or self.environment,
            "run_as": check_enum(run_as, ServiceScriptUser, "run_as") or self.run_as,
            "script_version": check_text(version, "version") or "",
        }

        if kwargs:  # pragma: no cover
            update_dict.update(**kwargs)

        update_dict = clean_empty_values(update_dict=update_dict)

        response = self._client._request(
            "PUT",
            self._client._build_url("service", service_id=self.id),
            json=update_dict,
        )

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError(f"Could not update Service {self}", response=response)

        self.refresh(json=response.json()["results"][0])

    def delete(self) -> None:
        """Delete this service.

        :raises APIError: if delete was not successful.
        """
        response = self._client._request(
            "DELETE", self._client._build_url("service", service_id=self.id)
        )

        if response.status_code != requests.codes.no_content:  # pragma: no cover
            raise APIError(f"Could not delete Service {self}", response=response)

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
            raise OSError(f"Could not locate python package to upload in '{pkg_path}'")

    def _upload(self, pkg_path):
        url = self._client._build_url("service_upload", service_id=self.id)

        with open(pkg_path, "rb") as pkg:
            response = self._client._request(
                "POST", url, files={"attachment": (os.path.basename(pkg_path), pkg)}
            )

        if response.status_code != requests.codes.accepted:  # pragma: no cover
            raise APIError(
                f"Could not upload script file (or kecpkg) to Service {self}",
                response=response,
            )

        self.refresh(json=response.json()["results"][0])

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
        full_path = os.path.join(target_dir or os.getcwd(), self.filename)

        url = self._client._build_url("service_download", service_id=self.id)
        response = self._client._request("GET", url)
        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError(
                f"Could not download script file from Service {self}", response=response
            )

        with open(full_path, "w+b") as f:
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
        return self._client.service_executions(
            service=self.id, scope=self.scope_id, **kwargs
        )


class ServiceExecution(Base):
    """
    A virtual object representing a KE-chain Service Execution.

    .. versionadded:: 1.13

    :ivar id: id of the service execution
    :type id: uuid
    :ivar name: name of the service to which the execution is associated
    :type name: str
    :ivar status: status of the service. One of :class:`ServiceExecutionStatus`
    :type status: str
    :ivar service: the :class:`Service` object associated to this service execution
    :type service: :class:`Service`
    :ivar service_id: the uuid of the associated Service object
    :type service_id: uuid
    :ivar user: (optional) username of the user that executed the service
    :type user: str or None
    :ivar activity_id: (optional) the uuid of the activity where the service was executed from
    :type activity_id: uuid or None
    """

    def __init__(self, json, **kwargs):
        """Construct a scope from provided json data."""
        super().__init__(json, **kwargs)
        del self.created_at
        del self.updated_at

        self.name = json.get("service_name")
        self.service_id = json.get("service")
        self.status: ServiceExecutionStatus = json.get("status", "")

        self.user = json.get("username")
        if json.get("activity") is not None:
            self.activity_id: Optional[str] = json["activity"].get("id")
        else:
            self.activity_id = None

        self.started_at: Optional[datetime] = parse_datetime(json.get("started_at"))
        self.finished_at: Optional[datetime] = parse_datetime(json.get("finished_at"))

        self._service: Optional[Service] = None

    def __repr__(self):  # pragma: no cover
        return f"<pyke ServiceExecution '{self.name}' id {self.id[-8:]}>"

    @property
    def service(self) -> Service:
        """Retrieve the `Service` object to which this execution is associated."""
        if not self._service:
            self._service = self._client.service(id=self.service_id)
        return self._service

    def terminate(self):
        """
        Terminate the Service execution.

        .. versionadded:: 1.13

        :return: None if the termination request was successful
        :raises APIError: When the service execution could not be terminated.
        """
        url = self._client._build_url(
            "service_execution_terminate", service_execution_id=self.id
        )
        response = self._client._request("GET", url, params=dict(format="json"))

        if response.status_code != requests.codes.accepted:  # pragma: no cover
            raise APIError(f"Could not terminate Service {self}", response=response)

    def get_log(self, target_dir=None, log_filename="log.txt"):
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

        url = self._client._build_url(
            "service_execution_log", service_execution_id=self.id
        )
        response = self._client._request("GET", url)
        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError(
                f"Could not download execution log of Service {self}", response=response
            )

        with open(full_path, "w+b") as f:
            for chunk in response:
                f.write(chunk)

    def get_notebook_url(self):
        """
        Get the url of the notebook, if the notebook is executed in interactive mode.

        .. versionadded:: 1.13

        :return: full url to the interactive running notebook as `basestring`
        :raises APIError: when the url cannot be retrieved.
        """
        url = self._client._build_url(
            "service_execution_notebook_url", service_execution_id=self.id
        )
        response = self._client._request("GET", url, params=dict(format="json"))

        if response.status_code != requests.codes.ok:
            raise APIError(
                f"Could not retrieve notebook url of Service {self}", response=response
            )

        data = response.json()
        url = data.get("results")[0].get("url")
        return url
