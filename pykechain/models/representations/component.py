from typing import List, Any, Dict, Callable

from jsonschema import validate

from pykechain.enums import _AllRepresentations, PropertyType
from pykechain.exceptions import IllegalArgumentError
from pykechain.models.representations.representation_base import BaseRepresentation
from pykechain.models.validators.validator_schemas import representation_jsonschema_stub


class RepresentationsComponent(object):
    """
    Aggregate class to use representations on an object.

    To add representations to a Pykechain class, create an instance of this class in its __init__() method.

    .. versionadded:: 3.7
    """

    def __init__(
        self, parent_object, representation_options: Dict, update_method: Callable
    ):
        """
        Extract the json with the representation options.

        :param parent_object: Object to which this representation component is attached
        :param representation_options: json with list of representations
        :param update_method: method of the parent_object that is used to update the representations
        """
        self._parent_object = parent_object
        self._repr_options = representation_options
        self._update_method = update_method  # type: Callable

        # Construct representation objects
        self._representations = []  # type: List['AnyRepresentation']
        representations_json = self._repr_options
        for representation_json in representations_json:
            self._representations.append(
                BaseRepresentation.parse(
                    obj=self._parent_object, json=representation_json
                )
            )

    def get_representations(self) -> List["AnyRepresentation"]:
        """
        Get list of representation objects.

        :return: list of Representations
        :raises IllegalArgumentError if representations are set with incorrect options
        """
        return self._representations

    def set_representations(self, representations: List["AnyRepresentation"]) -> None:
        """Set the representations."""
        self._validate_representations(representations)

        # set the internal representation list
        self._representations = list(set(representations))

        # dump to _json options
        self._dump_representations()

        # update the options to KE-chain backend
        self._update_method(self._repr_options)

    def _validate_representations(self, representations: Any):
        """Check provided representation inputs."""
        if not isinstance(representations, (tuple, list)):
            raise IllegalArgumentError(
                "Should be a list or tuple with Representation objects, "
                "got {}".format(type(representations))
            )

        for r in representations:
            if not isinstance(r, BaseRepresentation):
                raise IllegalArgumentError(
                    "Representation '{}' should be a Representation object".format(r)
                )
            if not _valid_object_type(r, self._parent_object):
                raise IllegalArgumentError(
                    "Representation '{}' can not be added to '{}'.".format(
                        r, self._parent_object
                    )
                )
            r.validate_json()

    def _dump_representations(self):
        """Dump the representations as json inside the _repr_options dictionary."""
        representations_json = []
        for r in self._representations:
            json_format = r.as_json()
            validate(json_format, representation_jsonschema_stub)
            representations_json.append(json_format)

        self._repr_options = representations_json


def _valid_object_type(representation: BaseRepresentation, obj: "Base") -> bool:
    """
    Check whether the representation can be used on the provided object.

    :param representation: representation to check
    :type representation: BaseRepresentation
    :param obj: object to attach the representation to
    :type obj: Base
    :return: True if feasible, False if not.
    :rtype bool
    """
    rtype = representation.rtype
    if rtype == _AllRepresentations.CUSTOM_ICON:
        from pykechain.models import Activity2, Scope2

        return isinstance(obj, (Activity2, Scope2))
    else:
        from pykechain.models import Property2

        if not isinstance(obj, Property2):
            return False
        else:
            if rtype == _AllRepresentations.BUTTON:
                return obj.type in [
                    PropertyType.SINGLE_SELECT_VALUE,
                    PropertyType.MULTI_SELECT_VALUE,
                ]
            elif rtype == _AllRepresentations.DECIMAL_PLACES:
                return obj.type == PropertyType.FLOAT_VALUE
            elif rtype == _AllRepresentations.SIGNIFICANT_DIGITS:
                return obj.type == PropertyType.FLOAT_VALUE
            elif rtype == _AllRepresentations.THOUSANDS_SEPARATOR:
                return obj.type in [PropertyType.INT_VALUE, PropertyType.FLOAT_VALUE]
            elif rtype == _AllRepresentations.LINK_TARGET:
                return obj.type == PropertyType.LINK_VALUE
            elif rtype == _AllRepresentations.AUTOFILL:
                return obj.type in [
                    PropertyType.DATETIME_VALUE,
                    PropertyType.DATE_VALUE,
                    PropertyType.TIME_VALUE,
                ]
            else:
                return False
