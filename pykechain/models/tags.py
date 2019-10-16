from abc import abstractmethod

from typing import Iterable, Text, Any, Optional, List

from pykechain.exceptions import IllegalArgumentError


class TagsMixin:
    """
    Mix-in class to enable the use of tags on an object.

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
        # type: () -> List[Text]
        """
        Get a list of tags, with each tag being a string.

        :return: list of tags
        :rtype list
        """
        return list(self._tags) if self._tags is not None else list()

    @tags.setter
    def tags(self, new_tags):
        # type: (Iterable[Text]) -> None
        if new_tags is not None:
            if not isinstance(new_tags, (list, tuple, set)) or not all(isinstance(t, Text) for t in new_tags):
                raise IllegalArgumentError("Provided tags should be a list, tuple or set of strings. "
                                           "Received type '{}'.".format(type(new_tags)))

            unique_tags = list(set(new_tags))
        else:
            unique_tags = list()

        self.edit(tags=unique_tags)
        self._tags = unique_tags

    def remove_tag(self, tag):
        # type: (Text) -> None
        """
        Remove a tag from the existing tags.

        :param tag: Tag to be removed from existing tags.
        :type tag: str
        :return: None
        """
        if not isinstance(tag, Text):
            raise IllegalArgumentError('Tag must be a string, received "{}".'.format(type(tag)))
        if tag not in self.tags:
            raise ValueError("Tag '{}' is not among the existing tags. Existing tags: '{}'.".format(
                tag, "', '".join(self.tags)))

        remaining_tags = self.tags
        remaining_tags.remove(tag)
        self.tags = remaining_tags

    def add_tag(self, tag):
        # type: (Text) -> None
        """
        Append a tag to the existing tags.

        :param tag: Tag to be added to the existing tags.
        :type tag: str
        :return: None
        """
        if not isinstance(tag, Text):
            raise IllegalArgumentError('Tag must be a string, received "{}".'.format(type(tag)))

        updated_tags = self.tags
        updated_tags.append(tag)
        self.tags = updated_tags

    def has_tag(self, tag):
        # type: (Text) -> bool
        """
        Check whether a tag is used.

        :param tag: Tag to be searched for.
        :return: boolean
        :rtype bool
        """
        if not isinstance(tag, Text):
            raise IllegalArgumentError('Tag must be a string, received "{}".'.format(type(tag)))
        return tag in self.tags
