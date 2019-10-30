import datetime

from pykechain.enums import PropertyType
from pykechain.exceptions import IllegalArgumentError
from pykechain.models.property2_datetime import DatetimeProperty2
from tests.classes import TestBetamax


class TestDateTime(TestBetamax):
    example_time = datetime.datetime.now()

    def setUp(self) -> None:
        super(TestDateTime, self).setUp()

        self.property_model = self.project.model('Bike').add_property(
            name='Testing date', property_type=PropertyType.DATETIME_VALUE)  # type: DatetimeProperty2
        self.property = self.project.part('Bike').property(name='Testing date')  # type: DatetimeProperty2

        self.property.value = self.example_time

    def tearDown(self):
        self.property_model.delete()
        super(TestDateTime, self).tearDown()

    def test_get_datetime(self):
        value = self.property.value

        self.assertIsInstance(value, str)

    def test_set_value_none(self):
        self.property.value = None

    def test_set_value_non_datetime(self):
        with self.assertRaises(IllegalArgumentError):
            self.property.value = '3'

    def test_set_value(self):
        self.property.value = self.example_time

    def test_to_datetime(self):
        date_time_value = self.property.to_datetime()

        self.assertIsInstance(date_time_value, datetime.datetime)
