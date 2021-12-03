from unittest import TestCase

from pykechain.enums import Enum


class FirstEnum(Enum):
    SLUG_1 = "first slug"


class SecondEnum(FirstEnum):
    SLUG_2 = "second slug"


class TestEnums(TestCase):
    def test_inheritance(self):
        values = SecondEnum.values()

        self.assertIn("first slug", values)
