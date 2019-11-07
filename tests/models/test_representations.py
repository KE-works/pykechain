from jsonschema import validate

from pykechain.models.validators.validator_schemas import options_json_schema
from tests.classes import SixTestCase


class TestValidatorJSON(SixTestCase):
    def test_valid_button_representation_json(self):
        options = dict(
            representations=[dict(
                rtype='buttonRepresentation',
                config=dict(
                    buttonRepresentation="dropdown",
                )
            )]
        )
        validate(options_json_schema, options)
