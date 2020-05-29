from abc import ABC
from typing import Optional, Text, List, TypeVar

from pykechain.models import BaseInScope

T = TypeVar('T')


class TreeObject(BaseInScope, ABC):
    """Object class to include methods used to traverse a tree-structure."""

    def __init__(self, json, **kwargs):
        """
        Initialize the object with attributes related to a tree-structure.

        :param json: data dict from KE-chain.
        """
        super().__init__(json=json, **kwargs)

        self.parent_id = json.get('parent_id', None)  # type: Optional[Text]

        self._cached_children = None  # type: Optional[List[T]]

    def __call__(self: T, *args, **kwargs) -> T:
        """Short-hand version of the `child` method."""
        return self.child(*args, **kwargs)

    def child(self: T,
              name: Optional[Text] = None,
              pk: Optional[Text] = None,
              **kwargs) -> T:
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
