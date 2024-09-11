import os
from typing import Any, List, Optional, Union

from pykechain.defaults import PARTS_BATCH_LIMIT
from pykechain.enums import (
    ScopeReferenceColumns,
    StoredFileCategory,
    StoredFileClassification,
)
from pykechain.exceptions import IllegalArgumentError
from pykechain.models import Activity, Scope, user
from pykechain.models.base_reference import (
    _ReferenceProperty,
    _ReferencePropertyInScope,
)
from pykechain.models.context import Context
from pykechain.models.form import Form
from pykechain.models.stored_file import StoredFile
from pykechain.models.value_filter import ScopeFilter
from pykechain.models.workflow import Status
from pykechain.utils import get_in_chunks, uniquify


class ActivityReferencesProperty(_ReferencePropertyInScope):
    """A virtual object representing a KE-chain Activity References property.

    .. versionadded:: 3.7
    """

    REFERENCED_CLASS = Activity

    def _retrieve_objects(self, **kwargs) -> List[Activity]:
        """
        Retrieve a list of Activities.

        :param kwargs: optional inputs
        :return: list of Activity2 objects
        """
        activities = []
        for activity_json in self._value:
            activity = Activity(client=self._client, json=activity_json)
            activity.refresh()  # To populate the object with all expected data
            activities.append(activity)
        return activities


class ScopeReferencesProperty(_ReferenceProperty):
    """A virtual object representing a KE-chain Scope References property.

    .. versionadded: 3.9
    """

    REFERENCED_CLASS = Scope

    def _retrieve_objects(self, **kwargs) -> List[Scope]:
        """
        Retrieve a list of Scopes.

        :param kwargs: optional inputs
        :return: list of Scope2 objects
        """
        scope_ids = self._validate_values()

        scopes = []
        if scope_ids:
            scopes = list()
            for chunk in get_in_chunks(scope_ids, PARTS_BATCH_LIMIT):
                scopes.extend(
                    list(self._client.scopes(id__in=",".join(chunk), status=None))
                )
        return scopes

    def set_prefilters(
        self,
        prefilters: List[ScopeFilter] = None,
        clear: Optional[bool] = False,
    ) -> None:
        """
        Set pre-filters on the scope reference property.

        :param prefilters: list of Scope Filter objects
        :type prefilters: list
        :param clear: whether all existing pre-filters should be cleared. (default = False)
        :type clear: bool

        :return: None
        """
        if prefilters is not None:
            if not isinstance(prefilters, list) or not all(
                isinstance(pf, ScopeFilter) for pf in prefilters
            ):
                raise IllegalArgumentError(
                    f"`prefilters` must be a list of ScopeFilter objects, `{prefilters}` is not."
                )
        else:
            prefilters = []

        if not clear:
            list_of_prefilters = ScopeFilter.parse_options(options=self._options)
        else:
            list_of_prefilters = list()

        list_of_prefilters += prefilters

        # Only update the options if there are any prefilters to be set, or if the original filters have to overwritten
        if list_of_prefilters or clear:
            self._options.update(ScopeFilter.write_options(filters=list_of_prefilters))
            self.edit(options=self._options)

    def get_prefilters(self) -> List[ScopeFilter]:
        """
        Return a list of ScopeFilter objects currently configured on the property.

        :return: list of ScopeFilter objects
        :rtype list
        """
        return ScopeFilter.parse_options(self._options)

    def set_active_filter_switch(self, switch_visible: bool):
        """
        Set the switch between active and inactive scopes on the scope reference property.

        :param switch_visible: trigger the switch of showing active or inactive scopes
        :type switch_visible: bool
        """
        self._options.update({"show_active_status_filter": switch_visible})
        self.edit(options=self._options)

    def set_columns(self, list_of_columns: List[ScopeReferenceColumns] = None):
        """
        Set the columns visible inside the Scope selection dialog.

        :param list_of_columns: all the columns possible of a Scope
        :type list_of_columns: List of columns
        """
        self._options.update({"columns": list_of_columns})
        self.edit(options=self._options)


class UserReferencesProperty(_ReferenceProperty):
    """A virtual object representing a KE-chain User References property.

    .. versionadded: 3.9
    """

    REFERENCED_CLASS = user.User

    def _validate_values(self) -> List[str]:
        """
        Check if the `_value` attribute has valid content.

        :return list of UUIDs:
        :rtype list
        """
        if not self._value:
            return []

        object_ids = []
        for value in self._value:
            if isinstance(value, dict) and "pk" in value or "id" in value:
                pk = str(value.get("pk", value.get("id")))
                object_ids.append(pk)
            elif isinstance(value, (int, str)):
                object_ids.append(str(value))
            else:  # pragma: no cover
                raise ValueError(
                    f'Value "{value}" must be a dict with field `pk` or a UUID.'
                )
        return object_ids

    def _retrieve_objects(self, **kwargs) -> List[user.User]:
        """
        Retrieve a list of Users.

        :param kwargs: optional inputs
        :return: list of User objects

        """
        user_ids = self._validate_values()

        users = []
        if user_ids:
            users = list()
            for chunk in get_in_chunks(user_ids, PARTS_BATCH_LIMIT):
                users.extend(list(self._client.users(id__in=",".join(chunk))))
        return users

    def value_ids(self) -> Optional[List[int]]:
        """
        Retrieve the referenced object UUIDs only.

        :return: list of UUIDs
        :rtype list
        """
        return [value.get("pk") for value in self._value] if self.has_value() else None


class FormReferencesProperty(_ReferencePropertyInScope):
    """A virtual object representing a KE-chain Form References property.

    .. versionadded:: 3.7
    """

    REFERENCED_CLASS = Form

    def _retrieve_objects(self, **kwargs) -> List[Form]:
        """
        Retrieve a list of Forms.

        :param kwargs: optional inputs
        :return: list of Form objects
        """
        forms = []
        for forms_json in self._value:
            form = Form(client=self._client, json=forms_json)
            form.refresh()  # To populate the object with all expected data
            forms.append(form)
        return forms


class ContextReferencesProperty(_ReferencePropertyInScope):
    """A virtual object representing a KE-chain Context References property.

    .. versionadded:: 3.7
    """

    REFERENCED_CLASS = Context

    def _retrieve_objects(self, **kwargs) -> List[Context]:
        """
        Retrieve a list of Contexts.

        :param kwargs: optional inputs
        :return: list of Context objects
        """
        contexts = []
        for contexts_json in self._value:
            context = Context(client=self._client, json=contexts_json)
            context.refresh()  # To populate the object with all expected data
            contexts.append(context)
        return contexts


class StatusReferencesProperty(_ReferenceProperty):
    """A virtual object representing a KE-chain Status References property.

    .. versionadded:: 3.19
    """

    REFERENCED_CLASS = Status

    def _retrieve_objects(self, **kwargs) -> List[Status]:
        """
        Retrieve a list of Statuses.

        :param kwargs: optional inputs
        :return: list of Status objects
        """
        statuses = []
        for status_json in self._value:
            status = Status(client=self._client, json=status_json)
            status.refresh()  # To populate the object with all expected data
            statuses.append(status)
        return statuses


class StoredFilesReferencesProperty(_ReferenceProperty):
    """A virtual object representing a KE-chain StoredFile References property."""

    REFERENCED_CLASS = StoredFile

    def _retrieve_objects(self, **kwargs) -> List[StoredFile]:
        """
        Retrieve a list of StoredFile.

        :param kwargs: optional inputs
        :return: list of StoredFile objects
        """
        if self._value:
            stored_files_ids = [sf.get("id") for sf in self._value]
            return self._client.stored_files(id__in=",".join(stored_files_ids))

    def clear(self) -> None:
        """
        Clear the stored files from the value of the property.

        Introduced in order to minimize the effect on custom scripts when converting
        from `AttachmentProperty` to `StoredFileReferenceProperty`.
        """
        if self.value:
            self.value = []

    @property
    def filename(self) -> Optional[Union[str, list]]:
        """Filename or list of filenames of the file(s) stored in the property."""
        if self.value:
            if len(self.value) == 1:
                return self.value[0].filename
            else:
                return [stored_file.filename for stored_file in self.value]
        else:
            return None

    def download(self, directory: str, **kwargs):
        """Download stored files from the StoredFileReferenceProperty.

        Downloads multiple files in the provided directory and names them according to the
        filename. If multiple files have the same name, it makes them unique.

        :param directory: Directory path
        :type directory: basestring
        """
        for stored_file in self.value:
            filename = uniquify(os.path.join(directory, stored_file.filename))
            stored_file.save_as(filename=filename, **kwargs)

    def upload(self, data: Any) -> None:
        """Upload a stored file to the StoredFileReferenceProperty.

        :param data: File path
        :type data: basestring
        :raises APIError: When unable to upload the file to KE-chain
        :raises OSError: When the path to the file is incorrect or file could not be found
        """
        filename = os.path.basename(data)
        stored_file = self._client.create_stored_file(
            name=filename,
            scope=self.scope,
            classification=StoredFileClassification.SCOPED,
            category=StoredFileCategory.REFERENCED,
            filepath=data,
        )
        self.value = self.value + [stored_file] if self.value else [stored_file]


class SignatureProperty(_ReferenceProperty):
    """A virtual object representing a KE-chain StoredFile References property."""

    REFERENCED_CLASS = StoredFile

    @property
    def value(self) -> Optional[StoredFile]:
        """
        Retrieve the signature of this signature property.

        :return: an optional `StoredFile` object containing the signature.
        :rtype StoredFile
        """
        if not self._value:
            return None
        elif not self._cached_values:
            self._cached_values = self._retrieve_object()
        return self._cached_values

    @value.setter
    def value(self, value: Any) -> None:
        # This serialize_value helper function returns a list of value
        value: List[Any] = self.serialize_value(value)
        if value and isinstance(value, list):
            value = value[0]  # de-list this temp_value
        if self.use_bulk_update:
            self._pend_update(dict(value=value))
            self._value = dict(id=value) if isinstance(value, str) else None
            self._cached_values = None
        else:
            self._put_value(value)

    def _retrieve_object(self, **kwargs) -> StoredFile:
        return self._retrieve_objects(**kwargs)

    def _retrieve_objects(self, **kwargs) -> StoredFile:
        """
        Retrieve a StoredFile which contains the signature.

        :param kwargs: optional inputs
        :return: list of StoredFile objects
        """
        if self._value:
            stored_files_id = self._value.get("id")
            return self._client.stored_file(id=stored_files_id)

    def clear(self) -> None:
        """
        Clear the signature from the value of the property.

        Introduced in order to minimize the effect on custom scripts when converting
        from `AttachmentProperty` to `StoredFileReferenceProperty`.
        """
        if self.value:
            self.value = None

    @property
    def filename(self) -> Optional[Union[str, list]]:
        """Filename of the file stored in the signature property."""
        if self.value:
            return self.value.filename
        else:
            return None

    def download(self, directory: str, **kwargs):
        """Download stored files from the SignatureProperty.

        Downloads multiple files in the provided directory and names them according to the
        filename. If multiple files have the same name, it makes them unique.

        :param directory: Directory path
        :type directory: basestring
        """
        stored_file = self.value
        filename = uniquify(os.path.join(directory, stored_file.filename))
        stored_file.save_as(filename=filename, **kwargs)

    def upload(self, data: Any) -> None:
        """Upload a stored file to the SignatureProperty.

        :param data: File path
        :type data: basestring
        :raises APIError: When unable to upload the file to KE-chain
        :raises OSError: When the path to the file is incorrect or file could not be found
        """
        filename = os.path.basename(data)
        stored_file = self._client.create_stored_file(
            name=filename,
            scope=self.scope,
            classification=StoredFileClassification.SCOPED,
            category=StoredFileCategory.REFERENCED,
            filepath=data,
        )
        self.value = stored_file
