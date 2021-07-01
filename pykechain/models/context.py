from datetime import datetime
from typing import Dict, List, Optional, Text, Union

import requests

from pykechain.enums import ContextGroup, ContextType
from pykechain.exceptions import APIError
from pykechain.models import BaseInScope
from pykechain.models.input_checks import (check_base, check_datetime, check_enum, check_list_of_base,
                                           check_list_of_text, check_text, check_type)
from pykechain.models.tags import TagsMixin
from pykechain.typing import ObjectID, ObjectIDs
from pykechain.utils import Empty, clean_empty_values, empty, parse_datetime


class Context(BaseInScope, TagsMixin):
    """
    A virtual object representing a KE-chain Context.

    .. versionadded:: 3.12
    """

    def __init__(self, json, **kwargs):
        """Construct a service from provided json data."""
        super(Context, self).__init__(json, **kwargs)

        self.ref = json.get("ref")  # type: Text
        self.description = json.get("description", "")  # type:Text
        self.context_type = json.get("context_type")  # type: ContextType
        self.options = json.get("options", dict())  # type: Dict
        self.context_group = json.get("context_group", "")  # type: ContextGroup
        self._tags = json.get("tags")

        # associated activities
        self.activities = json.get("activities")  # type: ObjectIDs

        # LocationContext
        # these attributes are enabled when context_type == STATIC_LOCATION
        self.feature_collection = json.get("feature_collection", dict())  # type: dict

        # TimeperiodContext
        # these attributes are enabled when context_type == TIME_PERIOD
        self.start_date = parse_datetime(json.get("start_date"))  # type: Optional[datetime]
        self.due_date = parse_datetime(json.get("due_date"))  # type: Optional[datetime]

    def edit(
            self,
            name: Optional[Union[Text, Empty]] = empty,
            description: Optional[Union[Text, Empty]] = empty,
            tags: Optional[List[Union[Text, Empty]]] = empty,
            context_group: Optional[Union[ContextGroup, Empty]] = empty,
            scope: Optional[Union['Scope', ObjectID]] = empty,
            options: Optional[dict] = empty,
            activities: Optional[Union[List['Activity'], ObjectIDs]] = empty,
            feature_collection: Optional[dict] = empty,
            start_date: Optional[datetime] = empty,
            due_date: Optional[datetime] = empty,
            **kwargs
    ) -> 'self':
        """
        Edit the Context.

        :param name: Name of the Context to be displayed to the end-user.
        :param scope: Scope object or Scope Id where the Context is active on.
        :param description: (optional) description of the Context
        :param activities: (optional) associated list of Activity or activity object ID
        :param tags: (optional) tags
        :param context_group: (optional) a context context_group of the choices of `ContextGroup`
        :param options: (optional) dictionary with options.
        :param feature_collection: (optional) dict with a geojson feature collection to store for a STATIC_LOCATION
        :param start_date: (optional) start datetime for a TIME_PERIOD context
        :param due_date: (optional) start datetime for a TIME_PERIOD context
        :return: a created Context Object
        :return: The updated Context object
        """
        from pykechain.models import Scope
        from pykechain.models import Activity
        update_dict = {
            "name": check_text(name, "name"),
            "description": check_text(description, "description"),
            "scope": check_base(scope, Scope, "scope"),
            "tags": check_list_of_text(tags, "tags"),
            "context_group": check_enum(context_group, ContextGroup, "context_group"),
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
            self, activities: Optional[List[Union['Activity', ObjectIDs]]] = empty, **kwargs
    ):
        """
        Link a context to one or more activities.

        :param activities: optional list of Activities or object Id's from activities.
        :returns: updated context objects
        """
        from pykechain.models import Activity
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
            self, activities: Optional[List[Union['Activity', ObjectIDs]]] = empty, **kwargs
    ):
        """
        Unlink a context to one or more activities.

        :param activities: optional list of Activities or object Id's from activities.
        :returns: updated context objects
        """
        from pykechain.models import Activity
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
