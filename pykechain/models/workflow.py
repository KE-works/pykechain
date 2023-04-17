from typing import TYPE_CHECKING, List, Optional, Union

import requests

from pykechain.defaults import API_EXTRA_PARAMS
from pykechain.enums import StatusCategory, TransitionType, WorkflowCategory
from pykechain.exceptions import APIError, IllegalArgumentError
from pykechain.models import Base, BaseInScope
from pykechain.models.base import CrudActionsMixin, NameDescriptionTranslationMixin
from pykechain.models.input_checks import (
    check_base,
    check_enum,
    check_list_of_base,
    check_text,
    check_type,
)
from pykechain.models.tags import TagsMixin
from pykechain.typing import ObjectID
from pykechain.utils import Empty, clean_empty_values, find_obj_in_list

if TYPE_CHECKING:
    from pykechain.client import Client
    from pykechain.models import Scope


class Transition(Base, CrudActionsMixin):
    """Transition Object."""

    url_detail_name = "transition"
    url_list_name = "transitions"
    url_pk_name = "transition_id"

    def __init__(self, json, **kwargs) -> None:
        """Initialise a Transition object."""
        super().__init__(json, **kwargs)
        self.description: str = json.get("description", "")
        self.ref: str = json.get("ref", "")
        self.derived_from_id: Optional[ObjectID] = json.get("derived_from")

        self.from_status: List[Status] = [
            Status(j, client=self._client) for j in json.get("grom_status", [])
        ]
        self.to_status: Status = json.get("to_status")
        self.transition_type: TransitionType = json.get("transition_type")

        self.conditions: dict = json.get("conditions", {})
        self.validators: dict = json.get("validators", {})
        self.post_functions: dict = json.get("post_functions", {})
        self.transition_screen_id: Optional[ObjectID] = json.get("transition_screen")

    @classmethod
    def list(cls, client: "Client", **kwargs) -> List["Transition"]:
        """Retrieve a list of Transition objects through the client."""
        return super().list(client=client, **kwargs)

    @classmethod
    def get(cls, client: "Client", **kwargs) -> "Transition":
        """Retrieve a Transition object through the client."""
        return super().get(client=client, **kwargs)


class Status(Base, CrudActionsMixin):
    """Status object."""

    url_detail_name = "status"
    url_list_name = "statuses"
    url_pk_name = "status_id"

    def __init__(self, json, **kwargs) -> None:
        """Initialize a Status object."""
        super().__init__(json, **kwargs)
        self.description: str = json.get("description", "")
        self.ref: str = json.get("ref", "")
        self.status_category: StatusCategory = json.get("status_category")

    @classmethod
    def list(cls, client: "Client", **kwargs) -> List["Status"]:
        """Retrieve a list of Status objects through the client."""
        return super().list(client=client, **kwargs)

    @classmethod
    def get(cls, client: "Client", **kwargs) -> "Status":
        """Retrieve a Status object through the client."""
        return super().get(client=client, **kwargs)


class Workflow(
    BaseInScope, CrudActionsMixin, TagsMixin, NameDescriptionTranslationMixin
):
    """Workflow object."""

    url_detail_name = "workflow"
    url_list_name = "workflows"
    url_pk_name: str = "workflow_id"

    def __init__(self, json, **kwargs) -> None:
        """Initialize a Workflow Object."""
        super().__init__(json, **kwargs)
        self.description: str = json.get("description", "")
        self.ref: str = json.get("ref", "")
        self.derived_from_id: Optional[ObjectID] = json.get("derived_from_id")
        self._transitions: List[Transition] = [
            Transition(j, client=self._client) for j in json.get("transitions", [])
        ]
        self.category: WorkflowCategory = json.get("category")
        self.options: dict = json.get("options", {})
        self.active: bool = json.get("active")
        self._statuses: List[Status] = [
            Status(j, client=self._client) for j in json.get("statuses")
        ]

    def __repr__(self) -> str:  # pragma: no cover
        return f"<pyke Workflow '{self.name}' '{self.category}' id {self.id[-8:]}>"

    def edit(
        self, name: str = Empty(), description: str = Empty(), *args, **kwargs
    ) -> None:
        """Change the workflow object.

        Change the name and description of a workflow. It is also possible to update the workflow
        options and also the 'active' flag. To change the active flag of the workflow we
        kindly refer to the `activate()` and `deactivate()` methods on the workflow.

        :type name: name of the workflow is required.
        :type description: (optional) description of the workflow

        """
        if isinstance(name, Empty):
            name = self.name
        data = {
            "name": check_text(name, "name"),
            "description": check_text(description, "description"),
            "active": check_type(kwargs.get("active", Empty()), bool, "active"),
            "options": check_type(kwargs.get("options", Empty()), bool, "options"),
        }
        url = self._client._build_url("workflow", workflow_id=self.id)
        query_params = API_EXTRA_PARAMS.get(self.url_list_name)
        response = self._client._request(
            "PUT",
            url=url,
            params=query_params,
            json=clean_empty_values(data, nones=False),
        )
        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not edit the workflow", response=response)
        self.refresh(json=response.json()["results"][0])

    @classmethod
    def list(cls, client: "Client", **kwargs) -> List["Workflow"]:
        """Retrieve a list of Workflow objects through the client."""
        return super().list(client=client, **kwargs)

    @classmethod
    def get(cls, client: "Client", **kwargs) -> "Workflow":
        """Retrieve a single Workflow object using the client."""
        return super().get(client=client, **kwargs)

    def delete(self):
        """Delete Workflow."""
        return super().delete()

    @classmethod
    def create(
        cls,
        client: "Client",
        name: str,
        scope: Union["Scope", ObjectID],
        category: WorkflowCategory = WorkflowCategory.DEFINED,
        description: str = None,
        options: dict = None,
        active: bool = False,
        **kwargs,
    ) -> "Workflow":
        """
        Create a new Workflow object using the client.

        :param client: Client object.
        :param name: Name of the workflow
        :param scope: Scope of the workflow
        :param category: (optional) category of the workflow, defaults to WorkflowCategory.DEFINED
        :param description: (optional) description of the workflow
        :param options: (optional) JSON/dictionary with workflow options
        :param active: (optional) boolean flag to set the workflow to active. Defaults to False
        :param kwargs: (optional) additional kwargs.
        :return: a Workflow object
        :raises APIError: When the Workflow could not be created.
        """
        from pykechain.models import Scope  # avoiding circular imports here.

        data = {
            "name": check_text(name, "name"),
            "scope": check_base(scope, Scope, "scope"),
            "category": check_enum(category, WorkflowCategory, "category"),
            "description": check_text(description, "description"),
            "options": check_type(options, dict, "options"),
            "active": check_type(active, bool, "active"),
        }
        kwargs.update(API_EXTRA_PARAMS[cls.url_list_name])
        response = client._request(
            "POST", client._build_url(cls.url_list_name), params=kwargs, json=data
        )

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError(f"Could not create {cls.__name__}", response=response)

        return cls(json=response.json()["results"][0], client=client)

    @property
    def status_order(self) -> List[Status]:
        """Statuses in the right order."""
        return self.statuses

    @status_order.setter
    def status_order(self, value: List[Union[ObjectID, Status]]):
        """
        Set the order of the statuses specifically in a certain order.

        :param value: a determined ordered list of Status or status UUID's
        """
        if not value:
            raise IllegalArgumentError(
                f"To set the order of statises, provide a list of status objects, got: '{value}'"
            )
        data = {"status_order": check_list_of_base(value, Status, "statuses")}
        url = self._client._build_url("workflow_set_status_order", workflow_id=self.id)
        response = self._client._request("PUT", url=url, json=data)
        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError(
                "Could not alter the order of the statuses", response=response
            )
        self.refresh(json=response.json()["results"][0])

    #
    # Subclass finders and managers.
    #

    def transition(
        self,
        value: str = None,
        attr: str = None,
    ) -> Transition:
        """
        Retrieve the Transition belonging to this workflow based on its name, ref or uuid.

        :param value: transition name, ref or UUID to search for
        :param attr: the attribute to match on. E.g. to_status=<Status Obj>
        :return: a single :class:`Transition`
        :raises NotFoundError: if the `Transition` is not part of the `Workflow`
        :raises MultipleFoundError

        Example
        -------
        >>> workflow = project.workflow('Simple Flow')
        >>> transition = workflow.transition('in progress')
        >>> todo_status = client.status(name="To Do")
        >>> transition = workflow.transition(todo_status, attr="to_status")

        """
        return find_obj_in_list(value, iterable=self._transitions, attribute=attr)

    @property
    def transitions(self):
        """
        Retrieve the Transitions belonging to this workflow.

        :return: multiple :class:`Transition`
        """
        return self._transitions

    def status(self, value: str = None, attr: str = None) -> Status:
        """
        Retrieve the Status belonging to this workflow based on its name, ref or uuid.

        :param value: status name, ref or UUID to search for
        :param attr: the attribute to match on.
        :return: a single :class:`Status`
        :raises NotFoundError: if the `Status` is not part of the `Workflow`
        :raises MultipleFoundError

        Example
        -------
        >>> workflow = project.workflow('Simple Flow')
        >>> status = workflow.status('To Do')

        """
        return find_obj_in_list(value, iterable=self._statuses, attribute=attr)

    @property
    def statuses(self):
        """
        Retrieve the Statuses belonging to this workflow.

        :return: multiple :class:`Status`
        """
        return self._statuses

    #
    # Mutable methods on the object
    #

    def activate(self):
        """Set the active status to True."""
        if not self.active:
            url = self._client._build_url("workflow_activate", workflow_id=self.id)
            response = self._client._request("PUT", url=url)
            if response.status_code != requests.codes.ok:  # pragma: no cover
                raise APIError("Could not activate the workflow", response=response)

            # we need to do a full refresh here from the server as the
            # API of workflow/<id>/activate does not return the full object as response.
            self.refresh(
                url=self._client._build_url("workflow", workflow_id=self.id),
                extra_params=API_EXTRA_PARAMS.get(self.url_list_name),
            )

    def deactivate(self):
        """Set the active status to False."""
        if self.active:
            url = self._client._build_url("workflow_deactivate", workflow_id=self.id)
            response = self._client._request("PUT", url=url)
            if response.status_code != requests.codes.ok:  # pragma: no cover
                raise APIError("Could not activate the workflow", response=response)

            # we need to do a full refresh here from the server as the
            # API of workflow/<id>/deactivate does not return the full object as response.
            self.refresh(
                url=self._client._build_url("workflow", workflow_id=self.id),
                extra_params=API_EXTRA_PARAMS.get(self.url_list_name),
            )

    def clone(
        self,
        target_scope: "Scope" = Empty(),
        name: Optional[str] = Empty(),
        description: Optional[str] = Empty(),
    ) -> "Workflow":
        """Clone the current workflow into a new workflow.

        Also used to 'import' a catalog workflow into a scope.

        :param target_scope: (optional) target scope where to clone the Workflow to.
            Defaults current scope.
        :param name: (optional) name of the new workflow
        :param description: (optional) description of the new workflow
        """
        from pykechain.models import Scope

        if isinstance(target_scope, Empty):
            target_scope = self.scope_id
        data = {
            "target_scope": check_base(target_scope, Scope, "scope"),
            "name": check_text(name, "name"),
            "description": check_text(description, "description"),
        }
        url = self._client._build_url("workflow_clone", workflow_id=self.id)
        query_params = API_EXTRA_PARAMS.get(self.url_list_name)
        response = self._client._request(
            "POST",
            url=url,
            params=query_params,
            json=clean_empty_values(data, nones=False),
        )
        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not clone the workflow", response=response)
        return Workflow(json=response.json()["results"][0], client=self._client)

    def update_transition(
        self,
        transition: Union[Transition, ObjectID],
        name: Optional[str] = Empty(),
        description: Optional[str] = Empty(),
        from_status: Optional[List[str]] = Empty(),
    ) -> Transition:
        """Update a specific Transition in the current workflow.

        Update the transition inside the worfklow based on a transition_id.

        :param transition: Transition object or transition id to alter
        :param name: (optional) name to change
        :param description: (optional) description to change
        :param from_status: (optional) a list of from statuses to update
        """
        data = {
            "transition_id": check_base(transition, Transition, "transition_id"),
            "name": check_text(name, "name"),
            "decription": check_text(description, "description"),
            "from_status": check_list_of_base(from_status, Status, "from_statuses"),
        }
        url = self._client._build_url("workflow_update_transition", workflow_id=self.id)
        query_params = API_EXTRA_PARAMS.get(self.url_list_name)
        response = self._client._request(
            "POST", url=url, params=query_params, json=data
        )
        if response.status_code != requests.codes.ok:
            raise APIError(
                f"Could not update the specific transition '{transition}' in the "
                "workflow",
                response=response,
            )
        # an updated transition will be altered, so we want to refresh the workflow.
        self.refresh()
        return Transition(json=response.json()["results"][0])

    def delete_transition(self, transition: Union[Transition, ObjectID]) -> None:
        """Remove Transition from the current Workflow and delete it.

        If the Transition is still connected to *other* Workflows, it will *not* be
        removed, and will result in a 400 reporting all attached Workflows.

        :param transition: object or uuid of a transition to delete.
        """
        transition_id = check_base(transition, Transition, "transition_id")
        url = self._client._build_url(
            "workflow_delete_transition",
            workflow_id=self.id,
            transition_id=transition_id,
        )
        query_params = API_EXTRA_PARAMS.get(self.url_list_name)
        response = self._client._request("DELETE", url=url, params=query_params)
        if response.status_code != requests.codes.no_content:
            raise APIError(
                f"Could not delete the specific transition '{transition}' from the "
                "workflow",
                response=response,
            )
        # a deleted transition will be unlinked, so we want to refresh the workflow.
        self.refresh()

    def create_transition(
        self,
        name: str,
        to_status: Union[Status, ObjectID],
        transition_type: TransitionType = TransitionType.GLOBAL,
        from_status: Optional[List[Union[Status, ObjectID]]] = Empty(),
        description: Optional[str] = Empty(),
    ):
        """
        Create a new Transition and associate it to the current Workflow.

        :param name: name of the transition.
        :param to_status: status where to transition to (a single status or status id)
        :param transition_type: transition type to transition to. (defaults to Global)
        :param from_status: (optional) status to transition from. Not used for Global transitions.
        :param description: (optional) description.
        """
        data = {
            "name": check_text(name, "name"),
            "to_status": check_base(to_status, Status, "to_status"),
            "transition_type": check_enum(
                transition_type, TransitionType, "transition_type"
            ),
            "from_status": check_list_of_base(from_status, Status, "from_statuses"),
            "description": check_text(description, "description"),
        }
        url = self._client._build_url("workflow_create_transition", workflow_id=self.id)
        query_params = API_EXTRA_PARAMS.get(self.url_list_name)
        response = self._client._request(
            "POST", url=url, params=query_params, json=clean_empty_values(data)
        )
        if response.status_code != requests.codes.created:
            raise APIError(
                "Could not create the specific transition in the " "workflow",
                response=response,
            )
        # a new transition will be linked to the workflow, so we want to refresh the workflow.
        self.refresh()
        return Transition(json=response.json()["results"][0], client=self._client)

    def create_status(
        self,
        name: str,
        category: StatusCategory = StatusCategory.UNDEFINED,
        description: Optional[str] = Empty(),
    ) -> Status:
        """Create a new Status.

        Will create a new status, a new global transition to that status and
        will link the new Global transition to that status to the current
        workflow.

        :param name: name of the status
        :param category: status category (defaults to UNDEFINED)
        :param description: (optional) description of the status
        """
        data = {
            "name": check_text(name, "name"),
            "status_category": check_enum(category, StatusCategory, "status_category"),
            "description": check_text(description, "description"),
        }

        url = self._client._build_url("workflow_create_status", workflow_id=self.id)
        query_params = API_EXTRA_PARAMS.get(self.url_list_name)
        response = self._client._request(
            "POST", url=url, params=query_params, json=clean_empty_values(data)
        )
        if response.status_code != requests.codes.created:
            raise APIError(
                "Could not create the specific status, a global transition and"
                "link it to the workflow",
                response=response,
            )
        # a new status will create a new global transition to that status,
        # so we want to update the current workflow.
        self.refresh()
        return Status(json=response.json()["results"][0], client=self._client)

    def link_transitions(self, transitions: List[Union[Transition, ObjectID]]):
        """
        Link a list of Transitions to a Workflow.

        :param transitions: a list of Transition Objects or transition_ids to link to the workflow.
        """
        data = {"transitions": check_list_of_base(transitions, Transition)}
        url = self._client._build_url("workflow_link_transitions", workflow_id=self.id)
        query_params = API_EXTRA_PARAMS.get(self.url_list_name)
        response = self._client._request(
            "POST", url=url, params=query_params, json=data
        )
        if response.status_code != requests.codes.ok:
            raise APIError(
                "Could not create the specific status, a global transition and"
                "link it to the workflow",
                response=response,
            )
        self.refresh(json=response.json()["results"][0])

    def unlink_transitions(
        self, transitions: List[Union[Transition, ObjectID]]
    ) -> None:
        """
        Unlink a list of Transitions to a Workflow.

        :param transitions: a list of Transition Objects or transition_ids to link to the workflow.
        """
        data = {"transitions": check_list_of_base(transitions, Transition)}
        url = self._client._build_url(
            "workflow_unlink_transitions", workflow_id=self.id
        )
        query_params = API_EXTRA_PARAMS.get(self.url_list_name)
        response = self._client._request(
            "POST", url=url, params=query_params, json=data
        )
        if response.status_code != requests.codes.ok:
            raise APIError(
                "Could not create the specific status, a global transition and"
                "link it to the workflow",
                response=response,
            )
        self.refresh(json=response.json()["results"][0])
