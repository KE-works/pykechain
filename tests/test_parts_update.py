import os

from pykechain.exceptions import IllegalArgumentError, NotFoundError
from pykechain.models import Part
from tests.classes import TestBetamax


class TestPartUpdate(TestBetamax):

    def setUp(self):
        super().setUp()
        self.model = self.project.model("Wheel")
        bike = self.project.part("Bike")
        self.wheel = bike.add(model=self.model, name='_WHEEL')  # type: Part

    def tearDown(self):
        self.wheel.delete()
        super().tearDown()

    def test(self):
        update_dict = {
            'Diameter': 432.1,
            'Spokes': 0,
            'Rim Material': 'Adamantium'
        }
        self.wheel.update(
            name='Better wheel',
            update_dict=update_dict,
        )
        live_wheel = self.project.part(pk=self.wheel.id)
        self.assertEqual(live_wheel.name, 'Better wheel')

        for name, value in update_dict.items():
            self.assertEqual(value, live_wheel.property(name=name).value,
                             "property {} with value {} did not match contents with KEC".format(name, value))

    def test_model(self):
        update_dict = {
            'Diameter': 432.1,
            'Spokes': 0,
            'Rim Material': 'Adamantium'
        }
        self.model.update(update_dict=update_dict)

    def test_with_missing_property(self):
        update_dict = {
            'Unknown Property': 'Woot!'
        }
        with self.assertRaises(NotFoundError):
            self.wheel.update(update_dict=update_dict)

    # noinspection PyTypeChecker
    def test_invalid_inputs(self):
        with self.assertRaises(IllegalArgumentError):
            self.wheel.update(name=12)

        with self.assertRaises(IllegalArgumentError):
            self.wheel.update(update_dict=("Diameter", 41.2))

        with self.assertRaises(IllegalArgumentError):
            self.wheel.update(properties_fvalues=("Diameter", 41.2))

    # new in 1.14.1
    def test_with_property_ids(self):
        update_dict = dict()
        for p in self.wheel.properties:
            if p.name == 'Diameter':
                update_dict[p.id] = 1.5
            elif p.name == 'Spokes':
                update_dict[p.id] = 20
            elif p.name == 'Rim Material':
                update_dict[p.id] = "Adamantium"

        # do tests
        self.wheel.update(update_dict=update_dict)

    def test_with_attachment(self):
        # setup
        bike_part = self.project.part('Bike')  # type: Part
        bike_part.property(name='Picture').value = None

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)).replace('\\', '/'))
        attachment_path = project_root + '/requirements.txt'
        update_dict = {
            'Picture': attachment_path,
        }

        # do tests
        bike_part.update(update_dict=update_dict)
        bike_part.refresh()
        attachment_prop = bike_part.property(name='Picture')

        self.assertTrue(attachment_prop.has_value(), msg='Attachment was not uploaded.')
        self.assertIn('requirements', attachment_prop.filename, msg='filename changed.')

        # tearDown
        attachment_prop.value = None

    def test_bulk_update(self):
        from pykechain.models import Property
        Property.set_bulk_update(True)

        self.wheel.update(update_dict={
            'Diameter': 0.7,
            'Spokes': 25,
        })

        self.assertEqual(0.7, self.wheel.property("Diameter").value)
        self.assertEqual(25, self.wheel.property("Spokes").value)

        live_wheel = self.project.part(name="_WHEEL")

        self.assertIsNone(live_wheel.property("Diameter").value)
        self.assertIsNone(live_wheel.property("Spokes").value)

        Property.update_values(client=self.client)
        live_wheel.refresh()

        self.assertEqual(0.7, live_wheel.property("Diameter").value)
        self.assertEqual(25, live_wheel.property("Spokes").value)
