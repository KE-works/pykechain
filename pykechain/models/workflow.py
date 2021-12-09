from typing import Iterable, Optional

from pykechain.models import Base, BaseInScope
from pykechain.models.base import NameDescriptionTranslationMixin
from pykechain.models.tags import TagsMixin
from pykechain.typing import ObjectID


class Transition(Base, ):
    """Transition Object."""

    pass


class Status(Base):
    """Status object."""

    pass

class Workflow(BaseInScope, TagsMixin, NameDescriptionTranslationMixin):
    """Workflow object."""

    url_detail_name = "workflow"
    url_list_name = "workflows"

    def __init__(self, json, **kwargs):
        super().__init__(json, *kwargs)
        self.description = json.get("description", "")
        self.ref = json.get("ref", "")
        self.derived_from_id: Optional[ObjectID] = json.get("derived_from")
        self._transitions = json.get("transitions",[])
        self.category = json.get("category")
        self.options = json.get("options")
        self.active: bool = json.get("active")
        self.statuses = json.get("statuses")

    def __repr__(self):  # pragma: no cover
        return f"<pyke Workflow '{self.name}' '{self.category}' id {self.id[-8:]}>"

    def edit(self, tags: Optional[Iterable[str]] = None, *args, **kwargs) -> None:
        """Change the workflow object."""
        pass
