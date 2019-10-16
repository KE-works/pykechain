from abc import abstractmethod

from typing import Iterable, Text, Any, Optional

from pykechain.exceptions import IllegalArgumentError


class TagsMixin:
    """
    Intermediate class to enable the use of tags on an object.

    :ivar tags: list of tags
    :type tags: list
    """
    _tags = list()

    @abstractmethod
    def edit(self, tags=None, *args, **kwargs):
        # type: (Optional[Iterable[Text]], *Any, **Any) -> None
        pass

    @property
    def tags(self):
        return list(self._tags) if self._tags is not None else list()

    @tags.setter
    def tags(self, new_tags):
        # type: (Iterable[Text]) -> None
        if new_tags is not None:
            if not isinstance(new_tags, (list, tuple, set)) or not all(isinstance(t, Text) for t in new_tags):
                raise IllegalArgumentError('Tags must be provided as a list, tuple or set of strings!')

            # Enforce uniqueness of tags while maintaining order
            unique_tags = list()
            for tag in new_tags:
                if tag not in unique_tags:
                    unique_tags.append(tag)

        else:
            unique_tags = list()

        self.edit(tags=unique_tags)
        self._tags = unique_tags

    def remove_tag(self, tag):
        # type: (Text) -> None
        if not isinstance(tag, Text):
            raise IllegalArgumentError('Tag must be a string!')
        if tag not in self.tags:
            raise ValueError("Tag {} is not part of the tags!".format(tag))

        remaining_tags = self.tags
        remaining_tags.remove(tag)
        self.tags = remaining_tags

    def add_tag(self, tag):
        # type: (Text) -> None
        if not isinstance(tag, Text):
            raise IllegalArgumentError('Tag must be a string!')
        if tag in self.tags:
            raise ValueError("Tag {} is already part of the tags!".format(tag))

        updated_tags = self.tags
        updated_tags.append(tag)
        self.tags = updated_tags

    def has_tag(self, tag):
        # type: (Text) -> bool
        if not isinstance(tag, Text):
            raise IllegalArgumentError('Tag must be a string!')
        return tag in self.tags


class ConcreteTagsBase(TagsMixin):
    """
    Dummy implementation of the edit method allows for instantiation of the TagsMixin class.
    """

    def edit(self, tags=None, *args, **kwargs):
        return None
