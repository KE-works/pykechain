from io import BytesIO
from typing import List, TYPE_CHECKING, Text, Union

import requests

from pykechain.defaults import API_EXTRA_PARAMS
from pykechain.enums import StoredFileCategory, StoredFileClassification
from pykechain.exceptions import APIError
from pykechain.models import BaseInScope
from pykechain.models.base import CrudActionsMixin, NameDescriptionTranslationMixin
from pykechain.models.input_checks import check_base, check_enum, check_text
from pykechain.models.tags import TagsMixin
from pykechain.typing import ObjectID
from pykechain.utils import Empty, clean_empty_values

if TYPE_CHECKING:
    from pykechain.client import Client
    from pykechain.models import Scope
class StoredFile(
    BaseInScope, CrudActionsMixin, TagsMixin, NameDescriptionTranslationMixin
):
    """Stored File object"""

    url_upload_name = "upload_stored_file"
    url_detail_name = "stored_file"
    url_list_name = "stored_files"
    url_pk_name: str = "file_id"

    def __init__(self, json, **kwargs):
        """Initialize a Stored File Object."""
        super().__init__(json, **kwargs)

        self.category = json.get("category", "")
        self.classification = json.get("classification", "")
        self.content_type = json.get("content_type")
        self.description = json.get("description")
        self.name = json.get("name")

    def __repr__(self):  # pragma: no cover
        return f"<pyke StoredFile '{self.name}' id {self.id[-8:]}>"

    def edit(
        self,
        name: str = Empty(),
        description: str = Empty(),
        category: str = Empty(),
        classification: str = Empty(),
        *args,
        **kwargs
    ) -> None:
        """

        """
        if isinstance(name, Empty):
            name = self.name
        data = {
            "name": check_text(name, "name"),
            "scope": check_base(scope, Scope, "scope"),
            "description": check_text(description, "description"),
            "category": check_enum(category, StoredFileCategory, "category"),
            "classification": check_enum(classification, StoredFileClassification,
                                         "classification"),
        }

        query_params = API_EXTRA_PARAMS.get(self.url_list_name)
        response = self._client._request(
            method="PUT",
            url=self._client._build_url("stored_files", file_id=self.id),
            params=query_params,
            json=clean_empty_values(data, nones=False),
        )
        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not edit the stored file", response=response)
        self.refresh(json=response.json()["results"][0])

    @classmethod
    def list(cls, client: "Client", **kwargs) -> List["StoredFile"]:
        """Retrieve a list of Workflow objects through the client."""
        return super().list(client=client, **kwargs)

    @classmethod
    def get(cls, client: "Client", **kwargs) -> "StoredFile":
        """Retrieve a single Workflow object using the client."""
        return super().get(client=client, **kwargs)

    @classmethod
    def create(
        cls,
        client: "Client",
        name: str,
        filepath: str,
        scope: Union["Scope", ObjectID],
        category: StoredFileCategory = StoredFileCategory.GLOBAL,
        classification: StoredFileClassification = StoredFileClassification.GLOBAL,
        description: str = None,
        **kwargs,
    ) -> "StoredFile":
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
            "description": check_text(description, "description"),
            "category": check_enum(category, StoredFileCategory, "category"),
            "classification": check_enum(classification, StoredFileClassification, "classification"),
        }
        files = {
            "file": open(filepath, 'rb'),
        }
        kwargs.update(API_EXTRA_PARAMS[cls.url_upload_name])
        response = client._request(
            method="POST",
            url=client._build_url(cls.url_upload_name),
            data=data,
            files=files,
        )

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError(f"Could not create {cls.__name__}", response=response)

        return cls(json=response.json()["results"][0], client=client)

    def delete(self):
        """Delete Workflow."""
        return super().delete()


