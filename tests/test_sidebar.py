from pykechain.models.sidebar.sidebar_manager import SideBarManager
from tests.classes import TestBetamax


class TestSideBar(TestBetamax):

    def setUp(self):
        super(TestSideBar, self).setUp()

    def tearDown(self):
        super(TestSideBar, self).tearDown()

    def test_manager(self):
        side_bar_manager = SideBarManager(scope=self.project)

        self.assertIsInstance(side_bar_manager, SideBarManager)
