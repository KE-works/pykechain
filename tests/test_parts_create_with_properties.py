from pykechain.models import Part2
from pykechain.utils import is_uuid
from tests.classes import TestBetamax


class TestPartCreateWithProperties(TestBetamax):
    def test_create_part_with_properties_no_bulk(self):
        """Test create a part with the properties when bulk = False for old API compatibility"""
        parent = self.project.part('Bike')  # type: Part2
        wheel_model = self.project.model('Wheel')  # type: Part2

        update_dict = {
            'Diameter': 42.42,
            'Spokes': 42,
            'Rim Material': 'Unobtanium'
        }

        new_wheel = parent.add_with_properties(wheel_model, "Fresh Wheel", update_dict=update_dict, bulk=False)

        self.assertIsInstance(new_wheel, Part2)
        self.assertTrue(new_wheel.property('Diameter'), 42.42)

        new_wheel.delete()

    def test_create_part_with_properties_names_with_bulk(self):
        """Test create a part with the properties when bulk = False for old API compatibility"""
        parent = self.project.part('Bike')  # type: Part2
        wheel_model = self.project.model('Wheel')  # type: Part2

        update_dict = {
            'Diameter': 42.43,
            'Spokes': 42,
            'Rim Material': 'Unobtanium'
        }

        new_wheel = parent.add_with_properties(wheel_model, "Fresh Wheel", update_dict=update_dict, bulk=True)

        self.assertIsInstance(new_wheel, Part2)
        self.assertTrue(new_wheel.property('Diameter'), 42.43)

        new_wheel.delete()

    def test_create_part_with_properties_ids_with_bulk(self):
        """Test create a part with the properties when bulk = False for old API compatibility"""
        parent = self.project.part('Bike')  # type: Part2
        wheel_model = self.project.model('Wheel')  # type: Part2

        update_dict = {
            wheel_model.property('Diameter').id: 42.43,
            wheel_model.property('Spokes').id: 42,
            wheel_model.property('Rim Material').id: 'Unobtanium'
        }

        # check if the keys are really a UUID
        self.assertTrue(any([is_uuid(key) for key in update_dict.keys()]))

        new_wheel = parent.add_with_properties(wheel_model, "Fresh Wheel", update_dict=update_dict, bulk=True)

        self.assertIsInstance(new_wheel, Part2)
        self.assertTrue(new_wheel.property('Diameter'), 42.43)

        new_wheel.delete()
