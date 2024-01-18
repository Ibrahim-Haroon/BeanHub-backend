import pytest
from django.test import TestCase


@pytest.mark.skip(reason="Don't use admin so just dummy test")
class AdminTestCase(TestCase):
    def test_admin(self):
        pass

