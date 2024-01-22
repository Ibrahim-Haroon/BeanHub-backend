from django.test import TestCase, Client

class SwaggerTestCase(TestCase):
    def test_swagger_endpoint(self):
        client = Client()
        response = client.get('/swagger/?format=openapi')
        print(response.content)