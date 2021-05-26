from datetime import datetime
from typing import Text, Dict, Optional

from pykechain.enums import ContextTypes
from pykechain.models import BaseInScope
from pykechain.models.tags import TagsMixin
from pykechain.typing import ObjectIDs
from pykechain.utils import parse_datetime, empty, Empty


# TODO: make crud methods in the client
# TODO: make curd methods in the scope
# TODO: ensure that context_type is either location/time and enable/disable use of various attributes.
# TODO: write tests


class Context(BaseInScope, TagsMixin):
    def __init__(self, json, **kwargs):
        """Construct a service from provided json data."""
        super(Context, self).__init__(json, **kwargs)

        self.ref: Text = json.get("ref")
        self.description: Text = json.get("description", "")
        self.context_type: ContextTypes = json.get("context_type")
        self.options: Dict = json.get("options", dict())

        # associated activities
        self.activities: ObjectIDs = json.get("activities")

        # LocationContext
        # these attributes are enabled when context_type == STATIC_LOCATION
        self.feature_collection: Dict = json.get("feature_collection", dict())

        # TimeperiodContext
        # these attributes are enabled when context_type == TIME_PERIOD
        self.start_date: Optional[datetime] = parse_datetime(json.get("start_date"))
        self.due_date: Optional[datetime] = parse_datetime(json.get("due_date"))

    def edit(
            self,
            description: Optional[Text, Empty] = empty,
            tags=empty,
            scope=empty,
            # context_type=empty,
            options=empty,
            activities=empty,
            feature_collection=empty,
            start_date=empty,
            due_date=empty
    ):
        """
        Edit the Context.

        :param description:
        :param tags:
        :param scope:
        :param context_type:
        :param options:
        :param activities:
        :param feature_collection:
        :param start_date:
        :param due_date:
        :return:
        """
        pass

    def delete(self):
        """Delete the Context."""

        return self._client.delete_context(self)
