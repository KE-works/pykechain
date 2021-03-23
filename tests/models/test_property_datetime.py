import datetime

from pykechain.enums import PropertyType
from pykechain.exceptions import IllegalArgumentError
from pykechain.models import DatetimeProperty, Property
from tests.classes import TestBetamax


class TestDateTime(TestBetamax):
    example_time = datetime.datetime.now()
    NAME = "_TESTING DATE"

    def setUp(self) -> None:
        super(TestDateTime, self).setUp()

        self.bike_model = self.project.model('Bike')
        self.property_model = self.bike_model.add_property(
            name=self.NAME, property_type=PropertyType.DATETIME_VALUE)  # type: DatetimeProperty
        self.property = self.project.part('Bike').property(name=self.NAME)  # type: DatetimeProperty

        self.property.value = self.example_time

    def tearDown(self):
        self.property_model.delete()
        super(TestDateTime, self).tearDown()

    def test_get_datetime(self):
        value = self.property.value

        self.assertIsInstance(value, str)

    def test_set_value_none(self):
        self.property.value = None

    def test_set_value_iso_string(self):
        self.property.value = self.example_time.isoformat()

    def test_set_value_non_datetime(self):
        with self.assertRaises(IllegalArgumentError):
            self.property.value = '3'

    def test_set_value(self):
        self.property.value = self.example_time

    def test_pending_value(self):
        self.property.value = None

        Property.set_bulk_update(True)

        self.property.value = self.example_time

        live_property = self.project.property(id=self.property.id)
        self.assertFalse(live_property.has_value())

        Property.update_values(client=self.client)

        live_property.refresh()
        self.assertTrue(live_property.has_value())

    def test_value_via_part(self):
        self.bike_model.update(update_dict={
            self.NAME: self.example_time,
        })

    def test_to_datetime(self):
        date_time_value = self.property.to_datetime()

        self.assertIsInstance(date_time_value, datetime.datetime)

    def test_iso_formatted(self):
        date_time_value = self.property.to_datetime()

        iso_format_datetime = DatetimeProperty.to_iso_format(date_time_value)

        self.assertIsInstance(iso_format_datetime, str)

