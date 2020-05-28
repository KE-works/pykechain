from abc import abstractmethod
from typing import List, Any

from jsonschema import validate

from pykechain.exceptions import IllegalArgumentError, APIError
from pykechain.models.representations.representation_base import BaseRepresentation
from pykechain.models.validators.validator_schemas import options_json_schema


class RepresentationMixin(object):
    """
    Mixin class to use representations on an object.

    To add representations to a Pykechain class, it must be added in the class declaration:
        class Property(Base, RepresentationMixin)

    To properly load the representations on creation of the inheriting class, add a call to the initialization method
    after the options can be safely retrieved:
        RepresentationMixin.__init__(self, self._options.get('representations', {}))
    """

    _representations = list()  # type: List[BaseRepresentation]
    _repr_options = list()

    def __init__(self, representation_options):
        """
        Extract the json with the representation options.

        :param representation_options: json with list of representations
        """
        self._repr_options = representation_options

        # Construct representation objects
        self._representations = []
        representations_json = self._repr_options
        for representation_json in representations_json:
            self._representations.append(
                BaseRepresentation.parse(obj=self, json=representation_json)
            )

    @property
    def representations(self) -> List[BaseRepresentation]:
        """
        Provide and set list of representation objects.

        :return: list of Representations
        :raises IllegalArgumentError if representations are set with incorrect options
        """
        return self._representations

    @representations.setter
    def representations(self, representations: List[BaseRepresentation]) -> None:
        self._validate_representations(representations)

        # set the internal representation list
        self._representations = list(set(representations))

        # dump to _json options
        self._dump_representations()

        # update the options to KE-chain backend
        self._save_representations(self._repr_options)

    def _validate_representations(self, representations: Any):
        """Check provided representation inputs."""
        if not isinstance(representations, (tuple, list)):
            raise IllegalArgumentError('Should be a list or tuple with Representation objects, '
                                       'got {}'.format(type(representations)))

        for r in representations:
            if not isinstance(r, BaseRepresentation):
                raise IllegalArgumentError("Representation '{}' should be a Representation object".format(r))
            r.validate_json()

    def _dump_representations(self):
        """Dump the representations as json inside the _options dictionary with the key `representations`."""
        representations_json = []
        for representation in self._representations:
            if isinstance(representation, BaseRepresentation):
                representations_json.append(representation.as_json())
            else:
                raise APIError("representation is not a BaseRepresentation: '{}'".format(representation))

        [validate(r, options_json_schema) for r in representations_json]
        self._repr_options = representations_json

    @abstractmethod
    def _save_representations(self, representation_options):
        """Store the representation in the object."""
        # Implement this method via a subclass, e.g. "options()"
        pass
