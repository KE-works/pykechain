from typing import Iterable, List, Optional, Union

import requests

from pykechain.defaults import API_EXTRA_PARAMS
from pykechain.enums import WorkflowCategory
from pykechain.exceptions import NotFoundError
from pykechain.models import Base, BaseInScope, Scope
from pykechain.models.base import CrudActionsMixin, NameDescriptionTranslationMixin
from pykechain.models.input_checks import check_base, check_enum, check_text, check_uuid
from pykechain.models.tags import TagsMixin
from pykechain.typing import ObjectID


class Transition(Base):
    """Transition Object."""

    url_detail_name = "transition"
    url_list_name = "transitions"

    @classmethod
    def list(cls, client: "Client", **kwargs) -> List["Transition"]:
        """Retrieve a list of Transition objects through the client."""
        return super().list(client=client, **kwargs)

    @classmethod
    def get(cls, client: "Client", **kwargs) -> "Transition":
        """Retrieve a Transition object through the client."""
        return super().get(client=client, **kwargs)


class Status(Base):
    """Status object."""

    pass


class Workflow(BaseInScope, CrudActionsMixin, TagsMixin, NameDescriptionTranslationMixin):
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
            Transition(j, self._client) for j in json.get("transitions", [])
        ]
        self.category: WorkflowCategory = json.get("category")
        self.options: dict = json.get("options", {})
        self.active: bool = json.get("active")
        self.statuses: List[Status] = [
            Status(j, self._client) for j in json.get("statuses")
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
