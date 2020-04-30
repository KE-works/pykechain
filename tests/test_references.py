from pykechain.enums import PropertyType
from pykechain.models.property2_activity_reference import ActivityReferenceProperty
from tests.classes import TestBetamax


class TestReferences(TestBetamax):

    def test_base(self):
        pass

    def test_activity_reference(self):
        from pykechain.enums import Multiplicity
        root = self.project.model(name='Product')
        part = self.project.create_model(name='The part', parent=root, multiplicity=Multiplicity.ONE)
        ref = part.add_property(name='activity ref', property_type=PropertyType.ACTIVITY_REFERENCES_VALUE)

        self.assertIsInstance(ref, ActivityReferenceProperty)
