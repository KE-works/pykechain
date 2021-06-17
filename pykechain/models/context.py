from datetime import datetime
from typing import Text, Dict, Optional, Union, List

import requests

from pykechain.enums import ContextType
from pykechain.exceptions import APIError
from pykechain.models import BaseInScope, Activity, Scope
from pykechain.models.input_checks import (
    check_text,
    check_base,
    check_list_of_text,
    check_list_of_base,
    check_type,
    check_datetime,
)
from pykechain.models.tags import TagsMixin
from pykechain.typing import ObjectIDs
from pykechain.utils import parse_datetime, empty, Empty, clean_empty_values


# TODO: make crud methods in the client
# TODO: make curd methods in the scope
# TODO: ensure that context_type is either location/time and enable/disable use of various attributes.
# TODO: write tests


class Context(BaseInScope, TagsMixin):
    """
    A virtual object representing a KE-chain Context.

    .. versionadded:: 3.11
    """

    def __init__(self, json, **kwargs):
        """Construct a service from provided json data."""
        super(Context, self).__init__(json, **kwargs)

        self.ref = json.get("ref")  # type: Text
        self.description = json.get("description", "")  # type:Text
        self.context_type = json.get("context_type")  # type: ContextType
        self.options = json.get("options", dict())  # type: Dict
        self._tags = json.get("tags")

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
        name: Optional[Union[Text, Empty]] = empty,
        description: Optional[Union[Text, Empty]] = empty,
        tags: Optional[List[Union[Text, Empty]]] = empty,
        scope=empty,
        # context_type=empty,
        options=empty,
        activities=empty,
        feature_collection=empty,
        start_date=empty,
        due_date=empty,
        **kwargs
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
        update_dict = {
            "name": check_text(name, "name"),
            "description": check_text(description, "description"),
            "scope": check_base(scope, Scope, "scope"),
            "tags": check_list_of_text(tags, "tags"),
            "activities": check_list_of_base(activities, Activity, "activities"),
            "options": check_type(options, dict, "options"),
            "feature_collection": check_type(
                feature_collection, dict, "feature_collection"
            ),
            "start_date": check_datetime(start_date, "start_date"),
            "due_date": check_datetime(due_date, "due_date"),
        }

        if feature_collection is None:
            update_dict["feature_collection"] = {}

        if kwargs:  # pragma: no cover
            update_dict.update(kwargs)

        update_dict = clean_empty_values(update_dict=update_dict)

        url = self._client._build_url("context", context_id=self.id)

        response = self._client._request("PUT", url, json=update_dict)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError(
                "Could not update Context: {}".format(self), response=response
            )

        return self.refresh(json=response.json().get("results")[0])

    def link_activities(
        self, activities: Optional[List[Union[Activity, ObjectIDs]]] = empty, **kwargs
    ):
        """
        Link a context to one or more activities.

        :param activities: optional list of Activities or object Id's from activities.
        :returns: updated context objects
        """
        update_dict = {
            "activities": check_list_of_base(activities, Activity, "activities"),
        }
        if kwargs:  # pragma: no cover
            update_dict.update(kwargs)

        url = self._client._build_url("context_link_activities", context_id=self.id)
        response = self._client._request("POST", url, json=update_dict)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError(
                "Could not update Context: {}".format(self), response=response
            )

        return self.refresh(json=response.json().get("results")[0])

    def unlink_activities(
        self, activities: Optional[List[Union[Activity, ObjectIDs]]] = empty, **kwargs
    ):
        """
        Unlink a context to one or more activities.

        :param activities: optional list of Activities or object Id's from activities.
        :returns: updated context objects
        """
        update_dict = {
            "activities": check_list_of_base(activities, Activity, "activities"),
        }
        if kwargs:  # pragma: no cover
            update_dict.update(kwargs)

        url = self._client._build_url("context_unlink_activities", context_id=self.id)
        response = self._client._request("POST", url, json=update_dict)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError(
                "Could not update Context: {}".format(self), response=response
            )

        return self.refresh(json=response.json().get("results")[0])

    def delete(self):
        """Delete the Context."""
        return self._client.delete_context(self)
