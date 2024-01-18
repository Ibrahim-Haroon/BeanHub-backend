import pytest
from django.test import TestCase


@pytest.mark.skip(reason="Don't use serializers so just dummy test")
class SerializersTestCase(TestCase):
    def test_serializers(self):
        pass

