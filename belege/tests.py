from django.contrib.auth.models import User
from django.test import Client, TestCase

from belege import api_views as belege_api_views
from dboeannotation.urls import router

client = Client()

USER = {"username": "testuser", "password": "somepassword"}


class BelegTestCase(TestCase):
    fixtures = ["dump.json"]

    def setUp(self):
        """Create test user"""
        User.objects.create_user(**USER)

    def get_belege_endpoints(self):
        """Extract belege API endpoints from the router"""
        belege_viewsets = [
            belege_api_views.BelegViewSetElasticSearch,
            belege_api_views.CitationViewSet,
            belege_api_views.LautungViewSet,
            belege_api_views.LehnwortViewSet,
            belege_api_views.FacsimileViewSet,
        ]
        endpoints = []
        for prefix, viewset, basename in router.registry:
            if viewset in belege_viewsets:
                endpoints.append((f"/api/{prefix}/", viewset))
        return endpoints

    def get_detail_test_cases(self):
        """Generate detail view test cases from router configuration"""
        test_cases = []

        for endpoint, viewset in self.get_belege_endpoints():
            model = viewset.queryset.model
            lookup_field = getattr(viewset, "lookup_field", "pk")
            instance = model.objects.first()
            if instance:
                lookup_value = getattr(instance, lookup_field)
                test_cases.append((endpoint, lookup_value))

        return test_cases

    def test_001_index(self):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_002_api_list_views(self):
        """Test all API list views from belege.api_views"""
        endpoints = self.get_belege_endpoints()

        for endpoint, viewset in endpoints:
            with self.subTest(endpoint=endpoint):
                response = client.get(endpoint)
                self.assertEqual(
                    response.status_code,
                    200,
                    f"Expected 200 for {endpoint}, got {response.status_code}",
                )
                self.assertIn("results", response.json())

    def test_003_api_detail_views(self):
        """Test API detail views for belege ViewSets"""
        test_cases = self.get_detail_test_cases()

        for endpoint, lookup_value in test_cases:
            with self.subTest(endpoint=endpoint, lookup_value=lookup_value):
                url = f"{endpoint}{lookup_value}/"
                response = client.get(url)
                self.assertEqual(
                    response.status_code,
                    200,
                    f"Expected 200 for {url}, got {response.status_code}",
                )

    def test_004_api_post_not_allowed(self):
        """Test that POST (create) is not allowed on belege ViewSets"""
        client.login(username=USER["username"], password=USER["password"])

        # Exclude FacsimileViewSet as it still uses ModelViewSet
        endpoints = [
            endpoint
            for endpoint, viewset in self.get_belege_endpoints()
            if not endpoint.endswith("facsimiles/")
        ]

        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                response = client.post(endpoint, {}, content_type="application/json")
                self.assertEqual(
                    response.status_code,
                    405,
                    f"Expected 405 for POST to {endpoint}, got {response.status_code}",
                )
