from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar

import requests

from pykechain.exceptions import NotFoundError
from pykechain.models import BaseInScope

T = TypeVar("T")


class TreeObject(BaseInScope, ABC):
    """Object class to include methods used to traverse a tree-structure."""

    def __init__(self, json, **kwargs):
        """
        Initialize the object with attributes related to a tree-structure.

        :param json: data dict from KE-chain.
        """
        super().__init__(json=json, **kwargs)

        self.parent_id: Optional[str] = json.get("parent_id", None)
        self._parent: Optional[T] = None
        self._cached_children: Optional[List[T]] = None

    def __call__(self: T, *args, **kwargs) -> T:
        """Short-hand version of the `child` method."""
        return self.child(*args, **kwargs)

    def child(
        self: T, name: Optional[str] = None, pk: Optional[str] = None, **kwargs
    ) -> T:
        """
        Retrieve a child object.

        :param name: optional, name of the child
        :type name: str
        :param pk: optional, UUID of the child
        :type: pk: str
        :return: Child object
        :raises MultipleFoundError: whenever multiple children fit match inputs.
        :raises NotFoundError: whenever no child matching the inputs could be found.
        """
        raise NotImplementedError  # pragma: no cover

    def parent(self: T) -> T:
        """
        Retrieve the parent object.

        :return: Parent object
        :raises APIError: whenever the parent could not be retrieved
        """
        raise NotImplementedError  # pragma: no cover

    def siblings(self: T, **kwargs) -> List[T]:
        """
        Retrieve all objects that have the same parent as the current object, thereby including itself.

        :return: iterable of objects
        :raises NotFoundError: whenever the current object is a root object, thereby having no siblings.
        """
        raise NotImplementedError  # pragma: no cover

    def children(self: T, **kwargs) -> List[T]:
        """
        Retrieve all children objects.

        :return: iterable of child objects.
        :rtype Iterable
        :raises APIError:
        """
        raise NotImplementedError  # pragma: no cover

    def all_children(self: T) -> List[T]:
        """
        Retrieve a flat list of all descendants, sorted depth-first.

        :returns list of child objects
        :rtype List
        """
        all_children = list()

        for child in self.children():
            all_children.append(child)
            all_children.extend(child.all_children())

        return all_children

    @abstractmethod
    def count_children(self, method: str, **kwargs) -> int:
        """
        Retrieve the number of child objects using a light-weight request.

        :param method: which type of object to retrieve, either parts or activities
        :type method: str
        :return: number of child objects
        :rtype int
        """
        parameters = {"scope_id": self.scope_id, "parent_id": self.id, "limit": 1}
        if kwargs:
            parameters.update(kwargs)

        response = self._client._request(
            "GET", self._client._build_url(method), params=parameters
        )

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError(f"Could not retrieve {method}")

        count = response.json()["count"]

        return count

    def _populate_cached_children(
        self,
        all_descendants: List[T],
        overwrite: Optional[bool] = False,
    ) -> None:
        """
        Fill the `_cached_children` attribute with a list of descendants.

        :param all_descendants: list of TreeObject objects of possible descendants of this TreeObject.
        :type all_descendants: list
        :param overwrite: whether to remove existing cached children, defaults to False
        :type overwrite: bool
        :return: None
        """
        # Create mapping table from a parent ID to its children
        children_by_parent_id = dict()
        for descendant in all_descendants:
            if descendant.parent_id in children_by_parent_id:
                children_by_parent_id[descendant.parent_id].append(descendant)
            else:
                children_by_parent_id[descendant.parent_id] = [descendant]

        # Populate every descendant with its children
        for descendant in all_descendants:
            if descendant.id in children_by_parent_id:
                descendant._cached_children = children_by_parent_id[descendant.id]
            else:
                descendant._cached_children = []

        # Populate every descendant with its parent
        object_by_id = {c.id: c for c in all_descendants + [self]}
        for descendant in all_descendants:
            descendant._parent = object_by_id.get(descendant.parent_id)

        this_children = children_by_parent_id.get(self.id, list())
        if self._cached_children and not overwrite:
            self._cached_children.extend(this_children)
        else:
            self._cached_children = this_children
