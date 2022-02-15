from typing import Dict, List, Optional, Union

import requests

from pykechain.defaults import API_EXTRA_PARAMS
from pykechain.enums import FormCategory
from pykechain.exceptions import APIError, ForbiddenError
from pykechain.models import Activity, Scope
from pykechain.models.base import (
    Base,
    BaseInScope,
    CrudActionsMixin,
    NameDescriptionTranslationMixin,
)
from pykechain.models.context import Context
from pykechain.models.input_checks import check_base, check_list_of_base, check_text
from pykechain.models.tags import TagsMixin
from pykechain.models.workflow import Status
from pykechain.typing import ObjectID
from pykechain.utils import Empty, clean_empty_values, empty


class StatusForm(Base):
    """A virtual object representing a KE-chain StatusForm.

    A StatusForm is an intermediate object linking the Forms to its 'subforms', where each
    status of a form has a link to its Activity.
    """

    def __init__(self, json, **kwargs):
        """Construct a service from provided json data."""
        super().__init__(json, **kwargs)
        self.description: str = json.get("description", "")
        self.ref: str = json.get("ref", "")
        self.status: Status = Status(json.get("status"), client=self._client)
        self.activity: Activity = Activity(json.get("activity"), client=self._client)
        self.form: str = json.get("form")


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
        self.active: bool = json.get("active")
        self.category: FormCategory = json.get("category")
        self._status_forms: List[Dict] = json.get("status_forms", [])

    def __repr__(self):  # pragma: no cover
        return f"<pyke Form  '{self.name}' '{self.category}' id {self.id[-8:]}>"

    @classmethod
    def create_model(
        cls,
        client: "Client",
        name: str,
        scope: Union[Scope, ObjectID],
        workflow: Union["Workflow", ObjectID],
        contexts: List[Union[Context, ObjectID]],
        **kwargs: dict,
    ) -> "Form":
        """Create a new form model.

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

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError(f"Could not create {cls.__name__}", response=response)

        return cls(json=response.json()["results"][0], client=client)

    #
    # Concepts underneath the Form
    # StatusForms

    @property
    def status_forms(self):
        """Retrieve the Status Forms of this Form."""
        return [StatusForm(s, client=self._client) for s in self._status_forms]

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

    @property
    def is_model(self) -> bool:
        """Form is a Form Model or Form Template."""
        return self.category == FormCategory.MODEL

    @property
    def is_instance(self) -> bool:
        """Form is a Form Instance."""
        return self.category == FormCategory.INSTANCE

    @property
    def is_active(self) -> bool:
        """Form is an active Form."""
        return self.active is not None and self.active

    #
    # Form Model finders and searchers.
    #

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
        """Edit the details of a Form (model or instance).

        Setting an input to None will clear out the value (exception being name).

        :param name: optional name of the form to edit. Cannot be cleared.
        :type name: basestring or None or Empty
        :param description: (optional) description of the form. Can be cleared.
        :type description: basestring or None or Empty
        :param kwargs: (optional) additional kwargs that will be passed in the during the edit/update request
        :return: None
        :raises IllegalArgumentError: when the type or value of an argument provided is incorrect
        :raises APIError: in case an Error occurs
        """
        update_dict = {
            "id": self.id,
            "name": check_text(name, "name") or self.name,
            "description": check_text(description, "description") or "",
        }

        if kwargs:  # pragma: no cover
            update_dict.update(**kwargs)

        update_dict = clean_empty_values(update_dict=update_dict)
        try:
            response = self._client._request(
                "PUT",
                self._client._build_url("form", form_id=self.id),
                params=API_EXTRA_PARAMS["form"],
                json=update_dict,
            )
        except ForbiddenError:
            raise ForbiddenError("A form model with instances created cannot be edited")

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError(f"Could not update Form {self}", response=response)

        self.refresh(json=response.json().get("results")[0])

    def delete(self) -> None:
        """Delete this Form.

        :raises APIError: if delete was not successful.
        """
        response = self._client._request(
            "DELETE", self._client._build_url(self.url_detail_name, form_id=self.id)
        )

        if response.status_code != requests.codes.no_content:  # pragma: no cover
            raise APIError(f"Could not delete Form {self}", response=response)

    def instantiate(self, name: Optional[str], **kwargs) -> "Form":
        """Create a new Form instance based on a model."""
        if self.category != FormCategory.MODEL:
            raise APIError("Form should be of category MODEL")

        data_dict = {
            "name": check_text(name, "name") or self.name,
            "description": check_text(kwargs.get("description"), "description")
            or self.description,
            "contexts": check_list_of_base(kwargs.get("contexts"), Context, "contexts")
            or [],
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
            "contexts": check_list_of_base(kwargs.get("contexts"), Context, "contexts")
            or [],
        }
        if "description" in kwargs:
            data_dict["description"] = check_text(
                kwargs.get("description"), "description"
            )

        response = self._client._request(
            "POST",
            self._client._build_url("form_clone", form_id=self.id),
            params=API_EXTRA_PARAMS["forms"],
            json=data_dict,
        )

        if response.status_code != requests.codes.created:
            raise APIError(f"Could not clone this Form: {self}", response=response)

        return Form(response.json()["results"][0], client=self._client)

    def activate(self):
        """Put the form to active.

        Model Forms can be put to inactive. When the Form model is not active the form cannot be
        instantiated. This methods sets the form to active.
        """
        if not self.active:
            url = self._client._build_url("form_activate", form_id=self.id)
            response = self._client._request("PUT", url=url)
            if response.status_code != requests.codes.ok:  # pragma: no cover
                raise APIError("Could not activate the form", response=response)

            # we need to do a full refresh here from the server as the
            # API of form/<id>/activate does not return the full object as response.
            self.refresh(
                url=self._client._build_url("form", form_id=self.id),
                extra_params=API_EXTRA_PARAMS.get(self.url_list_name),
            )

    def deactivate(self):
        """Put the form to inactive.

        Model Forms can be put to inactive. When the Form model is not active the form cannot be
        instantiated.
        """
        if self.active:
            url = self._client._build_url("form_deactivate", form_id=self.id)
            response = self._client._request("PUT", url=url)
            if response.status_code != requests.codes.ok:  # pragma: no cover
                raise APIError("Could not activate the form", response=response)

            # we need to do a full refresh here from the server as the
            # API of form/<id>/deactivate does not return the full object as response.
            self.refresh(
                url=self._client._build_url("form", form_id=self.id),
                extra_params=API_EXTRA_PARAMS.get(self.url_list_name),
            )
