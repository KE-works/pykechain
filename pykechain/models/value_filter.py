from typing import Text, Union, Any, Optional

from pykechain.enums import FilterType, Category, PropertyType
from pykechain.exceptions import IllegalArgumentError, NotFoundError
from pykechain.models.input_checks import check_base, check_enum


class PropertyValueFilter(object):
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
        part_model: Optional['Part'] = None,
    ):
        """Create PropertyValueFilter instance."""
        from pykechain.models import Property

        property_model_id = check_base(property_model, Property, "property_model")
        check_enum(filter_type, FilterType, "filter_type")

        self.id = property_model_id
        self.value = value
        self.type = filter_type

        if part_model is not None:
            self.validate(part_model)

    def __repr__(self):
        return "PropertyValueFilter {}: {}".format(self.type, self.value)

    def format(self) -> Text:
        """Format PropertyValueFilter as a string."""
        return "{}:{}:{}".format(self.id, self.value, self.type)

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
            if prop.type == PropertyType.BOOLEAN_VALUE:
                self.value = str(self.value).lower()
