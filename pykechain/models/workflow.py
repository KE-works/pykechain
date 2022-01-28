from typing import Iterable, List, Optional, Union

import requests

from pykechain.defaults import API_EXTRA_PARAMS
from pykechain.enums import StatusCategory, TransitionType, WorkflowCategory
from pykechain.exceptions import APIError
from pykechain.models import Base, BaseInScope, Scope
from pykechain.models.base import CrudActionsMixin, NameDescriptionTranslationMixin
from pykechain.models.input_checks import check_base, check_list_of_base, check_text
from pykechain.models.tags import TagsMixin
from pykechain.typing import ObjectID
from pykechain.utils import Empty


class Transition(Base, CrudActionsMixin):
    """Transition Object."""

    url_detail_name = "transition"
    url_list_name = "transitions"
    url_pk_name = "transition_id"

    def __init__(self, json, **kwargs):
        super().__init__(json, *kwargs)
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

    def __init__(self, json, **kwargs):
        super().__init__(json, *kwargs)
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

    def __init__(self, json, **kwargs):
        super().__init__(json, *kwargs)
        self.description: str = json.get("description", "")
        self.ref: str = json.get("ref", "")
        self.derived_from_id: Optional[ObjectID] = json.get("derived_from")
        self.transitions: List[Transition] = [
            Transition(j, client=self._client) for j in json.get("transitions", [])
        ]
        self.category: WorkflowCategory = json.get("category")
        self.options: dict = json.get("options", {})
        self.active: bool = json.get("active")
        self.statuses: List[Status] = [
            Status(j, client=self._client) for j in json.get("statuses")
        ]

    def __repr__(self) -> str:  # pragma: no cover
        return f"<pyke Workflow '{self.name}' '{self.category}' id {self.id[-8:]}>"

    def edit(self, tags: Optional[Iterable[str]] = None, *args, **kwargs) -> None:
        """Change the workflow object."""
        pass

    @classmethod
    def list(cls, client: "Client", **kwargs) -> List["Workflow"]:
        """Retrieve a list of Workflow objects through the client."""
        return super().list(client=client, **kwargs)

    @classmethod
    def get(cls, client: "Client", **kwargs) -> "Workflow":
        """Retrieve a single Workflow object using the client."""
        return super().get(client=client, **kwargs)

    @property
    def status_order(self) -> List[Status]:
        return self.statuses

    @status_order.setter
    def status_order(self, value: List[Union[ObjectID, Status]]):
        """
        Set the order of the statuses specifically in a certain order.

        :param value: a determined ordered list of Status or status UUID's
        """
        data = {"status_order": check_list_of_base(value, Status, "statuses")}
        url = self._client._build_url("workflow_set_status_order", workflow_id=self.id)
        response = self._client._request("PUT", url=url, json=data)
        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError(
                "Could not alter the order of the statuses", response=response
            )
        self.refresh(json=response.json()["results"][0])

    def activate(self):
        """
        Set the active status to True.
        """
        if not self.active:
            url = self._client._build_url("workflow_activate", workflow_id=self.id)
            response = self._client._request("PUT", url=url)
            if response.status_code != requests.codes.ok:  # pragma: no cover
                raise APIError("Could not activate the workflow", response=response)
            self.refresh(json=response.json()["results"][0])

    def deactivate(self):
        """
        Set the active status to False.
        """
        if self.active:
            url = self._client._build_url("workflow_deactivate", workflow_id=self.id)
            response = self._client._request("PUT", url=url)
            if response.status_code != requests.codes.ok:  # pragma: no cover
                raise APIError("Could not activate the workflow", response=response)
            self.refresh(json=response.json()["results"][0])

    def clone(
        self,
        target_scope: "Scope",
        name: Optional[str] = Empty(),
        description: Optional[str] = Empty(),
    ) -> "Workflow":
        """Clone the current workflow into a new workflow.

        :param target_scope: target scope where to clone the Workflow to
        :param name: (optional) name of the new workflow
        :param description: (optional) description of the new workflow
        """
        data = {
            target_scope: check_base(target_scope, Scope, "scope"),
            name: check_text(name, "name"),
            description: check_text(description, "descrioption")
        }
        url = self._client._build_url("workflow_clone", workflow_id=self.id)
        query_params = API_EXTRA_PARAMS.get(self.url_list_name)
        response = self._client._request("POST", url=url, params=query_params, json=data)
        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not clone the workflow", response=response)
        return Workflow(json=response.json()["results"][0])

    def update_transition(self):
        ...

    def delete_transition(self):
        ...

    def create_transition(self):
        ...

    def create_status(self):
        ...

    def link_transition(self):
        ...

    def unlink_transition(self):
        ...
