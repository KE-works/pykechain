import warnings
from abc import abstractmethod
from typing import Text, Union, Any, Dict, List, Optional

from pykechain.enums import FilterType, Category, PropertyType
from pykechain.exceptions import IllegalArgumentError, NotFoundError
from pykechain.models.input_checks import check_base, check_enum, check_type, check_text


class BaseFilter(object):
    """Base class for any filters used in pykechain."""

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.format() == other.format()
        else:
            return False

    @abstractmethod
    def format(self) -> Text:  # pragma: no cover
        """Format a filter as a string."""
        pass

    @classmethod
    @abstractmethod
    def parse_options(cls, options: Dict) -> List['BaseFilter']:  # pragma: no cover
        """
        Convert the dict & string-based definition of a filter to a list of Filter objects.

        :param options: options dict from a property or meta dict from a widget.
        :return: list of Filter objects
        :rtype list
        """
        pass


class PropertyValueFilter(BaseFilter):
    """
    Property value filter, used for Part reference properties and filtered grid widgets.

    :ivar id: property model UUID
    :ivar value: value of the filter
    :ivar type: filter type
    """

    def __init__(
        self,
        property_model: Union[Text, 'Property'],
        value: Any,
        filter_type: FilterType,
    ):
        """Create PropertyValueFilter instance."""
        from pykechain.models import Property

        property_model_id = check_base(property_model, Property, "property_model")
        check_enum(filter_type, FilterType, "filter_type")

        self.id = property_model_id
        self.value = value
        self.type = filter_type

    def __repr__(self):
        return "PropertyValueFilter {}: {} ({})".format(self.type, self.value, self.id)

    def format(self) -> Text:
        """Format PropertyValueFilter as a string."""
        value = str(self.value).lower() if isinstance(self.value, bool) else self.value
        return "{}:{}:{}".format(self.id, value, self.type)

    def validate(self, part_model: 'Part') -> None:
        """
        Validate data of the PropertyValueFilter.

        :param part_model: Part model to which the filter will be applied.
        :returns None
        """
        from pykechain.models import Part

        check_base(part_model, Part, "part_model")

        try:
            prop = part_model.property(self.id)
        except NotFoundError:
            raise IllegalArgumentError(
                "Property value filters can only be set on properties belonging to the selected Part model.")

        if prop.category != Category.MODEL:
            raise IllegalArgumentError(
                'Property value filters can only be set on Property models, received "{}".'.format(prop))
        else:
            if prop.type == PropertyType.BOOLEAN_VALUE and self.type != FilterType.EXACT:
                warnings.warn("A PropertyValueFilter on a boolean property should use filter type `{}`".format(
                    FilterType.EXACT), Warning)

    @classmethod
    def parse_options(cls, options: Dict) -> List['PropertyValueFilter']:
        """
        Convert the dict & string-based definition of a property value filter to a list of PropertyValueFilter objects.

        :param options: options dict from a multi-reference property or meta dict from a filtered grid widget.
        :return: list of PropertyValueFilter objects
        :rtype list
        """
        check_type(options, dict, "options")

        prefilter_string = options.get("prefilters", {}).get("property_value")
        prefilter_string_list = prefilter_string.split(",") if prefilter_string else []

        prefilters = list()
        for pf_string in prefilter_string_list:
            prefilter_raw = pf_string.split(":")

            if len(prefilter_raw) == 1:   # FIXME encoding problem KE-chain
                prefilter_raw = pf_string.split("%3A")

            prefilters.append(PropertyValueFilter(*prefilter_raw))

        return prefilters


class ScopeFilter(BaseFilter):
    """
    Scope filter, used on scope reference properties.

    :ivar tag: string
    """

    def __init__(
            self,
            tag: Optional[Text] = None,
    ):
        """Create a ScopeFilter object."""
        self.tag = check_text(tag, "tag")

    def __repr__(self):
        return "ScopeFilter: tag: {}".format(self.tag)

    def format(self) -> Text:
        """Format ScopeFilter as a string."""
        return self.tag if self.tag else ""

    @classmethod
    def parse_options(cls, options: Dict) -> List['ScopeFilter']:
        """
        Convert the dict & string-based definition of a scope filter to a list of ScopeFilter objects.

        :param options: options dict from a scope reference property or meta dict from a scopes widget.
        :return: list of ScopeFilter objects
        :rtype list
        """
        check_type(options, dict, "options")

        filters_dict = options.get("prefilters", {})
        tags_string = filters_dict.get("tags__contains", "")
        tags = tags_string.split(",") if tags_string else []

        return [ScopeFilter(tag=tag) for tag in tags]
