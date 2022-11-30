import os

from pykechain.models import Activity
from pykechain.models.widgets import WidgetsManager
from tests.classes import TestBetamax


class TestPartsImport(TestBetamax):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)).replace('\\', '/'))

    def setUp(self):
        super(TestPartsImport, self).setUp()
        self.task = self.project.create_activity(name="widget_test_task")  # type: Activity
        self.wm = self.task.widgets()  # type: WidgetsManager
        self.imported_parts = list()
        self.file = self.project_root + '/tests/files/test_import_parts/Wheel.xlsx'

    def tearDown(self):
        for part in self.imported_parts:
            part.delete()
        self.task.delete()
        super(TestPartsImport, self).tearDown()

    def test_import_parts_from_client(self):
        part_model = self.project.model(name='Wheel')
        parent_instance = self.project.part(name='Bike')
        self.wm.add_filteredgrid_widget(
            part_model=part_model,
            parent_instance=parent_instance,
            edit=True,
            delete=True,
            all_writable=True,
            collapse_filters=False,
        )

        self.client.import_parts(
            model=part_model,
            parent=parent_instance,
            activity=self.task,
            file=self.file,
            async_mode=False
        )
        self.imported_parts = list(self.client.parts(name="Mid Wheel"))
        self.assertEqual(len(self.imported_parts), 1)
        mid_wheel = self.imported_parts[0]
        self.assertEqual(mid_wheel.property(name="Diameter").value, 65.4)
        self.assertEqual(mid_wheel.property(name="Spokes").value, 22)
        self.assertEqual(mid_wheel.property(name="Rim Material").value, "Titanium")
        self.assertEqual(mid_wheel.property(name="Tire Thickness").value, 2.3)

