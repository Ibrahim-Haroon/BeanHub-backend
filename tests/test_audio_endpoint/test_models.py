import pytest
from django.test import TestCase


@pytest.mark.skip(reason="Don't use model so just dummy test")
class ModelsTestCase(TestCase):
    def test_model(self):
        pass
