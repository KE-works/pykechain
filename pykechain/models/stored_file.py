import os
from typing import List, Optional, Union

import requests

from pykechain.defaults import API_EXTRA_PARAMS
from pykechain.enums import StoredFileCategory, StoredFileClassification, StoredFileSize
from pykechain.exceptions import APIError, IllegalArgumentError
from pykechain.models import BaseInScope
from pykechain.models.base import CrudActionsMixin, NameDescriptionTranslationMixin
from pykechain.models.input_checks import check_base, check_enum, check_text
from pykechain.models.tags import TagsMixin
from pykechain.models.validators.mime_types_defaults import predefined_mimes
from pykechain.typing import ObjectID
from pykechain.utils import Empty, clean_empty_values


class StoredFile(
    BaseInScope, CrudActionsMixin, TagsMixin, NameDescriptionTranslationMixin
):
    """Stored File object."""

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
        self.file = json.get("file")
        self.name = json.get("name")
        self.filename = os.path.basename(
            json.get("file").get("full_size").split("?", 1)[0]
        )

    def __repr__(self):  # pragma: no cover
        return f"<pyke StoredFile '{self.name}' id {self.id[-8:]}>"

    def edit(
        self,
        name: str = Empty(),
        description: str = Empty(),
        scope: Union["Scope", ObjectID] = Empty(),
        category: StoredFileCategory = Empty(),
        classification: StoredFileClassification = Empty(),
        *args,
        **kwargs,
    ) -> None:
        """Change the StoredFile object.

        Change the name, description, scope, category and classification of a
        StoredFile.

        :type name: name of the StoredFile is required.
        :type description: (optional) description of the StoredFile
        :type category: (optional) if left empty, it will not be affected
        :type classification: (optional) if left empty, it will not be affected
        :type scope: (optional) if left empty, it will not be affected

        """
        from pykechain.models import Scope

        if isinstance(name, Empty):
            name = self.name
        data = {
            "name": check_text(name, "name"),
            "scope": check_base(scope, Scope, "scope"),
            "description": check_text(description, "description"),
            "category": check_enum(category, StoredFileCategory, "category"),
            "classification": check_enum(
                classification, StoredFileClassification, "classification"
            ),
        }
        url = self._client._build_url("stored_file", file_id=self.id)
        response = self._client._request(
            method="PATCH",
            url=url,
            json=clean_empty_values(data, nones=True),
        )
        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not edit the stored file", response=response)
        self.refresh(json=response.json()["results"][0])

    @classmethod
    def list(cls, client: "Client", **kwargs) -> List["StoredFile"]:
        """Retrieve a list of StoredFiles objects through the client."""
        return super().list(client=client, **kwargs)

    @classmethod
    def get(cls, client: "Client", **kwargs) -> "StoredFile":
        """Retrieve a single StoredFile object using the client."""
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
        Create a new StoredFile object using the client.

        :param client: Client object.
        :param name: Name of the StoredFile
        :param scope: Scope of the StoredFile
        :param filepath: mandatory, a StoredFile must have an attachment
        :param category: (optional) category of the StoredFile, defaults to
                         StoredFileCategory.GLOBAL
        :param classification: (optional) classification of the StoredFile,
                               defaults to StoredFileClassification.GLOBAL
        :param description: (optional) description of the StoredFile
        :param kwargs: (optional) additional kwargs.
        :return: a StoredFile object
        :raises APIError: When the StoredFile could not be created.
        """
        from pykechain.models import Scope  # avoiding circular imports here.

        data = {
            "name": check_text(name, "name"),
            "scope": check_base(scope, Scope, "scope"),
            "description": check_text(description, "description"),
            "category": check_enum(category, StoredFileCategory, "category"),
            "classification": check_enum(
                classification, StoredFileClassification, "classification"
            ),
        }
        files = {"file": open(filepath, "rb")}
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
        """Delete StoredFile."""
        return super().delete()

    def upload(
        self,
        filepath: str,
    ):
        """
        Upload a file to the StoredFile object.

        :param filepath: File path
        :type filepath: basestring
        :raises APIError: When unable to upload the file to KE-chain
        :raises OSError: When the path to the file is incorrect or file could not be found
        """
        with open(filepath, "rb") as f:
            files = {"file": f.read()}
        from pykechain.models import Scope

        data = {
            "name": self.name,
            "classification": self.classification,
            "scope": check_base(self.scope, Scope, "scope"),
            "category": self.category,
        }
        response = self._client._request(
            method="POST",
            url=self._client._build_url(self.url_change_file, file_id=self.id),
            data=data,
            files=files,
        )
        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError(f"Could not create {self.__name__}", response=response)

    def save_as(
        self,
        filename: Optional[str] = None,
        size: StoredFileSize = StoredFileSize.FULL_SIZE,
        **kwargs,
    ) -> None:
        """Download the stored file attachment to a file.

        :param filename: (optional) File path. If not provided, will be saved to current working dir
                         with `self.filename`.
        :type filename: basestring or None
        :param size: Size of file
        :type size: see enum.StoredFileSize

        :raises APIError: When unable to download the data
        :raises OSError: When unable to save the data to disk
        """
        filename = filename or os.path.join(os.getcwd(), self.filename)
        with open(filename, "w+b") as f:
            for chunk in self._download(size=size, **kwargs):
                f.write(chunk)

    def _download(self, size: StoredFileSize.FULL_SIZE, **kwargs):
        if self.content_type in predefined_mimes["image/*"]:
            url = self.file.get(size, "full_size")
        else:
            url = self.file.get("source")

        response = requests.get(url)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not download property value.", response=response)

        return response
