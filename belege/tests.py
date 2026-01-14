from django.test import Client, TestCase

client = Client()


class BelegTestCase(TestCase):
    fixtures = ["dump.json"]

    def test_001_api_listviews(self):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
