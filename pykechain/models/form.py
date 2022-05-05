from typing import Dict, List, Optional, Union

import requests

from pykechain.defaults import API_EXTRA_PARAMS
from pykechain.enums import FormCategory
from pykechain.exceptions import APIError, ForbiddenError
from pykechain.models import Activity, Part, Scope
from pykechain.models.base import (
    Base,
    BaseInScope,
    CrudActionsMixin,
    NameDescriptionTranslationMixin,
)
from pykechain.models.context import Context
from pykechain.models.input_checks import (
    check_base,
    check_list_of_base,
    check_list_of_dicts,
    check_text,
)
from pykechain.models.tags import TagsMixin
from pykechain.models.workflow import Status, Transition
from pykechain.typing import ObjectID
from pykechain.utils import Empty, clean_empty_values, empty


class StatusForm(Base):
    """A virtual object representing a KE-chain StatusForm.

    A StatusForm is an intermediate object linking the Forms to its 'subforms', where each
    status of a form has a link to its Activity.
    """

    def __init__(self, json, **kwargs):
        """Construct a status form from provided json data."""
        super().__init__(json, **kwargs)
        self.description: str = json.get("description", "")
        self.ref: str = json.get("ref", "")
        self.status: Status = Status(json.get("status"), client=self._client)
        self.activity: Activity = Activity(json.get("activity"), client=self._client)
        self.form: str = json.get("form")

    def __repr__(self):  # pragma: no cover
        return f"<pyke StatusForm  '{self.status}' id {self.id[-8:]}>"


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
        self._status_assignees: List[Dict] = json.get(
            "status_assignees_has_widgets", []
        )
        self.contexts = json.get("contexts", [])
        self.context_groups = json.get("context_groups", [])

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
        self, name: Optional[str], target_scope: Optional[Scope] = None, **kwargs
    ) -> Optional["Form"]:
        """Clone a new Form model based on a model.

        If target_scope is specified and different  from the scope of the form, then use the
        `clone_cross_scope` endpoint. Otherwise, use the basic `clone` endpoint.

        """
        if self.category != FormCategory.MODEL:
            raise APIError("Form should be of category MODEL")
        data_dict = {
            "name": check_text(name, "name") or f"{self.name}",
            "contexts": check_list_of_base(kwargs.get("contexts"), Context, "contexts")
            or [],
        }
        if "description" in kwargs:
            data_dict.update(
                {"description": check_text(kwargs.get("description"), "description")}
            )

        if not target_scope or target_scope.id == self.scope_id:
            response = self._client._request(
                "POST",
                self._client._build_url("form_clone", form_id=self.id),
                params=API_EXTRA_PARAMS["forms"],
                json=data_dict,
            )
        else:
            data_dict.update({"target_scope": check_base(target_scope, Scope, "scope")})
            response = self._client._request(
                "POST",
                self._client._build_url("form_clone_cross_scope", form_id=self.id),
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

    def link_contexts(self, contexts: List[Union[Context, ObjectID]]):
        """
        Link a list of Contexts to a Form.

        :param contexts: a list of Context Objects or context_ids to link to the form.
        :raises APIError: in case an Error occurs when linking
        """
        data = {"contexts": check_list_of_base(contexts, Context)}
        url = self._client._build_url("form_link_contexts", form_id=self.id)
        query_params = API_EXTRA_PARAMS.get(self.url_list_name)
        response = self._client._request(
            "POST", url=url, params=query_params, json=data
        )
        if response.status_code != requests.codes.ok:
            raise APIError(
                "Could not link the specific contexts to the form",
                response=response,
            )
        self.refresh(json=response.json()["results"][0])

    def unlink_contexts(self, contexts: List[Union[Context, ObjectID]]):
        """
        Unlink a list of Contexts from a Form.

        :param contexts: a list of Context Objects or context_ids to unlink from the form.
        :raises APIError: in case an Error occurs when unlinking
        """
        data = {"contexts": check_list_of_base(contexts, Context)}
        url = self._client._build_url("form_unlink_contexts", form_id=self.id)
        query_params = API_EXTRA_PARAMS.get(self.url_list_name)
        response = self._client._request(
            "POST", url=url, params=query_params, json=data
        )
        if response.status_code != requests.codes.ok:
            raise APIError(
                "Could not unlink the specific contexts from the form",
                response=response,
            )
        self.refresh(json=response.json()["results"][0])

    def set_status_assignees(self, statuses: List[dict]):
        """
        Set a list of assignees on each status of a Form.

        :param statuses: a list of dicts, each one contains the status_id and the list of
        assignees. Available fields per dict:
            :param status: Status object
            :param assignees: List of User objects
        :raises APIError: in case an Error occurs when setting the status assignees

        Example
        -------
        When the `Form` is known, one can easily access its status forms ids and build a
        dictionary, as such:

        >>> for status_form in form.status_forms:
        >>>    status_dict = {
        >>>        "status": status_form.status,
        >>>        "assignees": [user_1, user_2]
        >>>    }
        >>>     status_assignees_list.append(status_dict)
        >>> self.form.set_status_assignees(statuses=status_assignees_list)

        """
        from pykechain.models import User

        check_list_of_dicts(
            statuses,
            "statuses",
            [
                "status",
                "assignees",
            ],
        )
        for status in statuses:
            status["status"] = check_base(status["status"], Status)
            status["assignees"] = check_list_of_base(status["assignees"], User)
        url = self._client._build_url("form_set_status_assignees", form_id=self.id)
        query_params = API_EXTRA_PARAMS.get(self.url_list_name)
        response = self._client._request(
            "POST", url=url, params=query_params, json=statuses
        )
        if response.status_code != requests.codes.ok:
            raise APIError(
                "Could not set the list of status assignees to the form",
                response=response,
            )
        self.refresh(json=response.json()["results"][0])

    def possible_transitions(self) -> List[Transition]:
        """Retrieve the possible transitions that may be applied on the Form.

        It will return the Transitions from the associated workflow are can be applied
        on the Form in the current status.
        :returns: A list with possible Transitions that may be applied on the Form.
        """
        workflow = self._client.workflow(id=self._workflow["id"])
        return workflow.transitions

    def apply_transition(self, transition: Transition):
        """Apply the transition to put the form in another state following a transition.

        Apply transition is to put the Form in another state. Only transitions that
        can apply to the form should have the 'from_status' to the current state. (or
        it is a Global transition). If applied the Form will be set in the 'to_state' of
        the Transition.

        :param transition: a Transition object belonging to the workflow of the Form
        :raises APIError: in case an Error occurs when applying the transition

        Example
        -------
        When the `Form` and `Workflow` is known, one can easily apply a transition on it, as such:

        >>> transition = workflow.transition("In progress")
        >>> form.apply_transition(transition=transition)

        """
        check_base(transition, Transition)

        url = self._client._build_url(
            "form_apply_transition", form_id=self.id, transition_id=transition.id
        )
        query_params = API_EXTRA_PARAMS.get(self.url_list_name)
        response = self._client._request(
            "POST",
            url=url,
            params=query_params,
        )
        if response.status_code != requests.codes.ok:
            raise APIError(
                "Could not transition the form",
                response=response,
            )
        self.refresh(json=response.json()["results"][0])

    def has_part(self, part: Part) -> bool:
        """Return boolean if given Part is part of the Form tree.

        Based on the Parts category, either the model or the instance tree is checked.

        :param part: a Part object
        :raises IllegalArgumentError: in case not a `Part` object is used when calling the method
        :raises APIError: in case an Error occurs when checking whether `Form` contains the `Part`
        """
        part_id = check_base(part, Part)

        url = self._client._build_url(
            "forms_has_part", form_id=self.id, part_id=part_id
        )
        response = self._client._request("GET", url=url)
        if response.status_code != requests.codes.ok:
            raise APIError(
                f"Could not process whether `Form` {self.id} has part {part_id}",
                response=response,
            )
        return response.json()["results"][0]["has_part"]

    def workflows_compatible_with_scope(self, scope: Scope):
        """Return workflows from target scope that are compatible with source workflow.

        :param scope: a Scope object
        :raises IllegalArgumentError: in case not a `Scope` object is used when calling the method
        :raises APIError: in case an Error occurs

        """
        scope_id = check_base(scope, Scope)

        url = self._client._build_url(
            "forms_compatible_within_scope", form_id=self.id, scope_id=scope_id
        )
        response = self._client._request("GET", url=url)
        if response.status_code != requests.codes.ok:
            raise APIError(
                "Could not retrieve the compatible workflows",
                response=response,
            )
        return response.json()["results"]
