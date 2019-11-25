import os

from pykechain.exceptions import IllegalArgumentError, NotFoundError
from tests.classes import TestBetamax


class TestPartUpdate(TestBetamax):
    # updated in 1.9
    def test_part_update_with_dictionary_without_name(self):
        # setup
        front_fork = self.project.part('Front Fork')  # type: Part
        saved_front_fork_properties = dict([(p.name, p.value) for p in front_fork.properties])

        # do tests
        update_dict = {
            'Material': 'Adamantium',
            'Height': 432.1,
            'Color': 'Earth Blue (new)'
        }
        front_fork.update(update_dict=update_dict)
        refreshed_front_fork = self.project.part(pk=front_fork.id)

        for prop in refreshed_front_fork.properties:
            self.assertIn(prop.name, update_dict, "property with {} should be in the update dict".format(prop.name))
            self.assertEqual(update_dict[prop.name], prop.value, "property {} with value {} did not match contents "
                                                                 "with KEC".format(prop.name, prop.value))

        # tearDown
        for prop_name, prop_value in saved_front_fork_properties.items():
            front_fork.property(prop_name).value = prop_value

    # new in 1.9
    def test_part_update_with_dictionary_including_name(self):
        # setup
        front_fork = self.project.part('Front Fork')  # type: Part
        saved_front_fork_properties = dict([(p.name, p.value) for p in front_fork.properties])

        # do tests
        update_dict = {
            'Material': 'Adamantium',
            'Height': 432.1,
            'Color': 'Earth Blue (new)'
        }
        front_fork.update(name='Better front fork', update_dict=update_dict)
        refreshed_front_fork = self.project.part(pk=front_fork.id)
        self.assertEqual(refreshed_front_fork.name, 'Better front fork')
        for prop in refreshed_front_fork.properties:
            self.assertIn(prop.name, update_dict, "property with {} should be in the update dict".format(prop.name))
            self.assertEqual(update_dict[prop.name], prop.value, "property {} with value {} did not match contents "
                                                                 "with KEC".format(prop.name, prop.value))

        with self.assertRaises(IllegalArgumentError):
            front_fork.update(name=12, update_dict=update_dict)

        # tearDown
        for prop_name, prop_value in saved_front_fork_properties.items():
            front_fork.property(prop_name).value = prop_value
        refreshed_front_fork.edit(name='Front Fork')

    def test_part_update_with_missing_property(self):
        # setup
        front_fork = self.project.part('Front Fork')  # type: Part
        saved_front_fork_properties = dict([(p.name, p.value) for p in front_fork.properties])

        # do tests
        update_dict = {
            'Unknown Property': 'Woot!'
        }
        with self.assertRaises(NotFoundError):
            front_fork.update(update_dict=update_dict)

        # tearDown
        for prop_name, prop_value in saved_front_fork_properties.items():
            front_fork.property(prop_name).value = prop_value

    # new in 1.14.1
    def test_part_update_with_property_ids(self):
        # setup
        front_fork = self.project.part('Front Fork')  # type: Part
        saved_front_fork_properties = dict([(p.name, p.value) for p in front_fork.properties])

        update_dict = dict()
        for p in front_fork.properties:
            if p.name == 'Color':
                update_dict[p.id] = 'Green'
            elif p.name == 'Material':
                update_dict[p.id] = 'Titanium'
            elif p.name == 'Height (mm)':
                update_dict[p.id] = '42'

        # do tests
        front_fork.update(update_dict=update_dict)

        # tearDown
        for prop_name, prop_value in saved_front_fork_properties.items():
            front_fork.property(prop_name).value = prop_value

    def test_part_update_with_attachment(self):
        # setup
        bike_part = self.project.part('Bike')  # type: Part2
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
