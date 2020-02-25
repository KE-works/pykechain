from abc import ABC
from typing import Optional, Text, List

from pykechain.models import Base


class TreeObject(Base, ABC):
    """Object class to include methods used to traverse a tree-structure."""

    def __init__(self, json, **kwargs):
        """
        Initialize the object with attributes related to a tree-structure.

        :param json: data dict from KE-chain.
        """
        super().__init__(json=json, **kwargs)

        self.parent_id = json.get('parent_id', None)  # type: Optional[Text]

        self._cached_children = None  # type: Optional[List['TreeObject']]

    def __call__(self, *args, **kwargs) -> 'TreeObject':
        """Short-hand version of the `child` method."""
        return self.child(*args, **kwargs)

    def child(self,
              name: Optional[Text] = None,
              pk: Optional[Text] = None,
              **kwargs) -> 'TreeObject':
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
        raise NotImplementedError

    def parent(self) -> 'TreeObject':
        """
        Retrieve the parent object.

        :return: Parent object
        :raises APIError: whenever the parent could not be retrieved
        """
        raise NotImplementedError

    def siblings(self, **kwargs) -> List['TreeObject']:
        """
        Retrieve all objects that have the same parent as the current object, thereby including itself.

        :return: iterable of objects
        :raises NotFoundError: whenever the current object is a root object, thereby having no siblings.
        """
        raise NotImplementedError

    def children(self, **kwargs) -> List['TreeObject']:
        """
        Retrieve all children objects.

        :return: iterable of child objects.
        :rtype Iterable
        :raises APIError:
        """
        raise NotImplementedError

    def all_children(self) -> List['TreeObject']:
        """
        Retrieve a flat list of all descendants, sorted depth-first.

        :returns list of child objects
        :rtype List
        """
        all_children = list(self.children())

        for child in self.children():
            all_children.extend(child.all_children())

        return all_children
