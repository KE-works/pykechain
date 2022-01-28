from typing import List, Optional, Union

import requests

from pykechain.defaults import API_EXTRA_PARAMS
from pykechain.enums import FormCategory
from pykechain.exceptions import APIError
from pykechain.models import Scope
from pykechain.models.base import BaseInScope, CrudActionsMixin, NameDescriptionTranslationMixin
from pykechain.models.context import Context
from pykechain.models.input_checks import check_base, check_list_of_base, check_text
from pykechain.models.tags import TagsMixin
from pykechain.typing import ObjectID
from pykechain.utils import Empty, empty


class StatusForm:
    """A virtual object representing a KE-chain StatusForm.

    A StatusForm is an intermediate object linking the Forms to its 'subforms', where each
    status of a form has a link to its Activity.
    """

    pass


class Form(BaseInScope, CrudActionsMixin, TagsMixin, NameDescriptionTranslationMixin):
    """
    A virtual object representing a KE-chain Form Collection.

    .. versionadded:: v3.20

    :ivar id: id of the form
    :ivar name: name of the form
    :ivar description: description of the form
    :ivar ref: reference (slugified name) of the form
    :ivar category: the category of the form (FormCategory.MODEL or FormCategory.INSTANCE)
    :ivar active_status: current active Status of the form
    :ivar form_model_root: the form model root Part
    :ivar form_instance_root: the form instance root Part
    :ivar model_id: the pk of the model of this form instance
    :ivar status_form: The StatusForms of this form
    :ivar created_at: datetime in UTC timezone when the form was created
    :ivar updated_at: datetime in UTC timezone when the form was last updated
    :ivar derived_from_id: (optional) id where the objects is derived from.
    """

    url_detail_name = "form"
    url_list_name = "forms"
    url_pk_name = "form_id"

    def __init__(self, json, **kwargs):
        """Construct a service from provided json data."""
        super().__init__(json, **kwargs)
        self.description: str = json.get("description", "")
        self.ref: str = json.get("ref", "")
        self._workflow = json.get("workflow")
        self.active_status: "Status" = json.get("active_status")
        self.form_model_root: "Part" = json.get("form_model_root")
        self.form_instance_root: "Part" = json.get("form_instance_root")
        self.model_id: "Form" = json.get("model")
        self.derived_from_id: Optional[ObjectID] = json.get("derived_from_id")
        self.category: FormCategory = json.get("category")
        self.status_forms: List[StatusForm] = json.get("status_forms", [])

    def __repr__(self):  # pragma: no cover
        return f"<pyke Form  '{self.name}' '{self.category}' id {self.id[-8:]}>"

    @classmethod
    def create_model(
        cls,
        client: "Client",
        name: str,
        scope: Union[Scope, ObjectID],
        workflow: Union["Workflow", ObjectID],
        contexts: Optional[List[Union[Context, ObjectID]]] = Empty(),
        **kwargs: dict
    ) -> "Form":
        """A New Form Model created in KE-chain.

        Needs scope, name, workflow.
        :param client: The client connection to KE-chain API
        :param name: Name of the new form model
        :param scope: Scope or scope_id where to create the form model
        :param workflow: Workflow or workflow_id of the workflow associated to the form model,
            should be in scope.
        :param contexts: A list of Context or context id's to link to the Form model.
        :param kwargs: Additional kwargs such as contexts.
        """
        from pykechain.models.workflow import Workflow
        data = {
            "name": check_text(name, "name"),
            "scope": check_base(scope, Scope, "scope"),
            "workflow": check_base(workflow, Workflow, "workflow"),
            "contexts": check_list_of_base(contexts, Context, "contexts"),
        }

        kwargs.update(API_EXTRA_PARAMS[cls.url_list_name])
        response = client._request(
            "POST", client._build_url(cls.url_list_name), params=kwargs, json=data
        )

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError(f"Could not create {cls.__name__}", response=response)

        return cls(json=response.json()["results"][0], client=client)

    #
    # @classmethod
    # def list(cls, client: "Client", **kwargs) -> List["Form"]:
    #     """Retrieve a list of Form objects through the client."""
    #     return super().list(client=client, **kwargs)
    #
    # @classmethod
    # def get(cls, client: "Client", **kwargs) -> "Form":
    #     """Retrieve a Form object through the client."""
    #     return super().get(client=client, **kwargs)

    def instances(self, **kwargs) -> [List["Form"]]:
        """Retrieve the instances of this Form Model."""
        if self.category == FormCategory.MODEL:
            return self._client.forms(
                model=self, category=FormCategory.INSTANCE, **kwargs
            )
        else:
            raise FileNotFoundError(
                f"Form '{self}' is not a model, hence it has no instances."
            )

    def instance(self, **kwargs) -> "Form":
        """Retrieve a single instance of a Form Model."""
        return self._client._retrieve_singular(self.instances, **kwargs)

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
        """Delete this Form.

        :raises APIError: if delete was not successful.
        """
        response = self._client._request(
            "DELETE", self._client._build_url(self.url_detail_name, form_id=self.id)
        )

        if response.status_code != requests.codes.no_content:  # pragma: no cover
            raise APIError(f"Could not delete Service {self}", response=response)

    def instantiate(self, name: Optional[str], **kwargs) -> "Form":
        """Create a new Form instance based on a model."""
        if self.category != FormCategory.MODEL:
            raise APIError("Form should be of category MODEL")

        data_dict = {
            "name": check_text(name, "name") or self.name,
            "description": check_text(kwargs.get("description"),
                                      "description") or self.description,
            "contexts": check_list_of_base(kwargs.get("contexts"), Context, "contexts") or [],
        }

        url = self._client._build_url("form_instantiate", form_id=self.id)
        query_params = API_EXTRA_PARAMS["forms"]

        response = self._client._request(
            "POST", url, params=query_params, json=data_dict
        )

        if response.status_code != requests.codes.created:
            raise APIError(
                f"Could not instantiate this Form: {self}", response=response
            )

        instantiated_form = Form(response.json()["results"][0], client=self._client)
        return instantiated_form

    def clone(
        self, name: Optional[str], target_scope: Optional[Scope], **kwargs
    ) -> Optional["Form"]:
        """Clone a new Form model based on a model."""
        if self.category != FormCategory.MODEL:
            raise APIError("Form should be of category MODEL")

        data_dict = {
            "name": check_text(name, "name") or f"{self.name}",
            "target_scope": check_base(target_scope, Scope, "scope"),
            "contexts": check_list_of_base(kwargs.get("contexts"), Context, "contexts") or [],
        }
        if "description" in kwargs:
            data_dict["description"] = check_text(kwargs.get("description"), "description")

        response = self._client._request(
            "POST",
            self._client._build_url("form_clone", form_id=self.id),
            params=API_EXTRA_PARAMS["forms"],
            json=data_dict
        )

        if response.status_code != requests.codes.created:
            raise APIError(
                f"Could not clone this Form: {self}", response=response
            )

        return Form(response.json()["results"][0], client=self._client)
