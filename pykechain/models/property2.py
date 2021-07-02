from pykechain.exceptions import _DeprecationMixin
from pykechain.models import Property


class Property2(Property, _DeprecationMixin):
    """A virtual object representing a KE-chain property.

    .. versionadded: 3.0
       This is a `Property` to communicate with a KE-chain 3 backend.

    :cvar bulk_update: flag to postpone update of properties until manually requested
    :ivar type: The property type of the property. One of the types described in :class:`pykechain.enums.PropertyType`
    :ivar category: The category of the property, either `Category.MODEL` of `Category.INSTANCE`
    :ivar description: description of the property
    :ivar unit: unit of measure of the property
    :ivar model: the id of the model (not the model object)
    :ivar output: a boolean if the value is configured as an output (in an activity)
    :ivar part: The (parent) part in which this property is available
    :ivar value: the property value, can be set as well as property
    :ivar validators: the list of validators that are available in the property
    :ivar is_valid: if the property conforms to the validators
    :ivar is_invalid: if the property does not conform to the validator
    """

    pass
