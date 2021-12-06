import os
from datetime import datetime

import requests
from typing import Dict, List, Optional, Union

from pykechain.enums import (
    FormCategory, ServiceScriptUser,
    ServiceExecutionStatus,
    ServiceType,
    ServiceEnvironmentVersion,
)
from pykechain.exceptions import APIError
from pykechain.models.base import Base, BaseInScope
from pykechain.models.input_checks import check_text, check_enum, check_type
from pykechain.models.tags import TagsMixin
from pykechain.typing import ObjectID
from pykechain.utils import parse_datetime, Empty, clean_empty_values, empty

class Workflow(BaseInScope, TagsMixin):
    pass

class Transition:
    pass

class Status:
    pass

class StatusForm:
    pass


class NameDescriptionTranslationMixin:
    pass


class Form(BaseInScope, TagsMixin, NameDescriptionTranslationMixin):

    url_detail_name = "form"
    url_list_name = "forms"

    """
    A virtual object representing a KE-chain Form Collection.

    .. versionadded:: v3.20

    :ivar id: id of the form
    :ivar name: name of the formcollection
    :ivar description: description of the service
    :ivar version: version number of the service, as provided by uploaded
    :ivar type: type of the service. One of the :class:`ServiceType`
    :ivar filename: filename of the service
    :ivar environment: environment in which the service will execute. One of :class:`ServiceEnvironmentVersion`
    :ivar updated_at: datetime in UTC timezone when the Service was last updated

    .. versionadded:: 3.0

    :ivar trusted: Trusted flag. If the kecpkg is trusted.
    :ivar run_as: User to run the script as. One of :class:`ServiceScriptUser`.
    :ivar verified_on: Date when the kecpkg was verified by KE-chain (if verification pipeline is enabled)
    :ivar verification_results: Results of the verification (if verification pipeline is enabled)
    """

    def __init__(self, json, **kwargs):
        """Construct a service from provided json data."""
        super().__init__(json, **kwargs)

        self.description = json.get("description", "")
        self.ref = json.get("ref", "")

        self._workflow: List[ObjectID] = json.get("workflow", None)
        self.active_status: "Status" = json.get("active_status")

        self.form_model_root: "Part" = json.get("form_model_root")
        self.form_instance_root: "Part" = json.get("form_instance_root")
        self.model_id: "Form" = json.get("model")

        self.category: FormCategory = json.get("category")
        self.status_forms: List[StatusForm] = json.get("status_forms", [])

    def __repr__(self):  # pragma: no cover
        return f"<pyke Form '{self.name}' id {self.id[-8:]}>"


    def edit(
        self,
        name: Optional[Union[str, Empty]] = empty,
        description: Optional[Union[str, Empty]] = empty,
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
        # update_dict = {
        #     "id": self.id,
        #     "name": check_text(name, "name") or self.name,
        #     "description": check_text(description, "description") or "",
        #     "trusted": check_type(trusted, bool, "trusted") or self.trusted,
        #     "script_type": check_enum(type, ServiceType, "type") or self.type,
        #     "env_version": check_enum(
        #         environment_version, ServiceEnvironmentVersion, "environment version"
        #     )
        #     or self.environment,
        #     "run_as": check_enum(run_as, ServiceScriptUser, "run_as") or self.run_as,
        #     "script_version": check_text(version, "version") or "",
        # }
        #
        # if kwargs:  # pragma: no cover
        #     update_dict.update(**kwargs)
        #
        # update_dict = clean_empty_values(update_dict=update_dict)
        #
        # response = self._client._request(
        #     "PUT", self._client._build_url(self.url_detail_name, form_id=self.id), json=update_dict
        # )
        #
        # if response.status_code != requests.codes.ok:  # pragma: no cover
        #     raise APIError(f"Could not update Service {self}", response=response)
        #
        # self.refresh(json=response.json()["results"][0])

    def delete(self) -> None:
        """Delete this service.

        :raises APIError: if delete was not successful.
        """
        response = self._client._request(
            "DELETE", self._client._build_url(self.url_detail_name, form_id=self.id)
        )

        if response.status_code != requests.codes.no_content:  # pragma: no cover
            raise APIError(f"Could not delete Service {self}", response=response)
