from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import get_resolver

from belege import api_views as belege_api_views
from belege.models import Annotation, Beleg, Citation
from belege.utils import annotate_text
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
        ]
        endpoints = []
        for prefix, viewset, basename in router.registry:
            if viewset in belege_viewsets:
                endpoints.append((f"/api/{prefix}/", viewset))
        return endpoints

    def get_stats_endpoints(self):
        """Extract stats endpoints from URL configuration"""
        resolver = get_resolver()
        stats_endpoints = []

        for pattern in resolver.url_patterns:
            if hasattr(pattern, "namespace") and pattern.namespace == "stats":
                for url_pattern in pattern.url_patterns:
                    endpoint = f"/stats/{url_pattern.pattern}"
                    stats_endpoints.append(endpoint)

        return stats_endpoints

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

    def test_stats_views(self):
        """Test all stats API endpoints return 200"""
        stats_endpoints = self.get_stats_endpoints()

        for endpoint in stats_endpoints:
            with self.subTest(endpoint=endpoint):
                response = client.get(endpoint)
                self.assertEqual(
                    response.status_code,
                    200,
                    f"Expected 200 for {endpoint}, got {response.status_code}",
                )

    def test_005_save_sets_has_internal_comment(self):
        beleg = Beleg.objects.create(
            dboe_id="test-has-internal-comment",
            internal_comment="Some internal note",
            has_internal_comment=False,
        )
        beleg.refresh_from_db()
        self.assertTrue(beleg.has_internal_comment)

        beleg.internal_comment = ""
        beleg.has_internal_comment = True
        beleg.save()
        beleg.refresh_from_db()
        self.assertFalse(beleg.has_internal_comment)

    def test_006_save_sets_has_scan(self):
        beleg = Beleg.objects.create(
            dboe_id="test-has-scan",
            scan=["scan-1.jpg"],
            has_scan=False,
        )
        beleg.refresh_from_db()
        self.assertTrue(beleg.has_scan)

        beleg.scan = []
        beleg.has_scan = True
        beleg.save()
        beleg.refresh_from_db()
        self.assertFalse(beleg.has_scan)

    def test_007_annotation_pos_list_endpoint(self):
        beleg = Beleg.objects.create(dboe_id="test-annotation-pos")
        citation = Citation.objects.create(
            dboe_id="test-cit-annotation-pos", beleg=beleg
        )
        Annotation.objects.create(
            kontext=citation,
            payload={"tokens": [{"text": "Haus", "pos": "Subst"}]},
            tool="test-tool",
            source_field="quote_text",
        )

        response = client.get("/api/annotation-pos/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("results", data)
        self.assertGreaterEqual(len(data["results"]), 1)

        annotation = next(
            item for item in data["results"] if item["tool"] == "test-tool"
        )
        self.assertEqual(annotation["source_field"], "quote_text")
        self.assertEqual(
            annotation["payload"]["tokens"][0], {"text": "Haus", "pos": "Subst"}
        )

    def test_008_annotation_pos_post_endpoint(self):
        client.login(username=USER["username"], password=USER["password"])

        beleg = Beleg.objects.create(dboe_id="test-annotation-pos-post")
        citation = Citation.objects.create(
            dboe_id="test-cit-annotation-pos-post", beleg=beleg
        )

        response = client.post(
            "/api/annotation-pos/",
            {
                "kontext": citation.dboe_id,
                "payload": {"tokens": [{"text": "gehen", "pos": "Verb"}]},
                "tool": "post-test-tool",
                "source_field": "quote_text",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            Annotation.objects.filter(
                kontext=citation,
                tool="post-test-tool",
                source_field="quote_text",
            ).exists()
        )

    def test_009_annotation_pos_delete_endpoint(self):
        client.login(username=USER["username"], password=USER["password"])

        beleg = Beleg.objects.create(dboe_id="test-annotation-pos-delete")
        citation = Citation.objects.create(
            dboe_id="test-cit-annotation-pos-delete", beleg=beleg
        )
        annotation = Annotation.objects.create(
            kontext=citation,
            payload={"tokens": [{"text": "Haus", "pos": "Subst"}]},
            tool="delete-test-tool",
            source_field="quote_text",
        )

        response = client.delete(f"/api/annotation-pos/{annotation.id}/")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Annotation.objects.filter(id=annotation.id).exists())

    def test_010_show_orig_xml(self):
        for x in Beleg.objects.all():
            url = f"/api/show-original-xml/{x.dboe_id}"
            response = client.get(url)
            self.assertEqual(response.status_code, 200)
        response = client.get("/api/show-original-xml/whatever")
        self.assertEqual(response.status_code, 404)

    def test_011_annotate_text_respects_input_order_and_first_occurrence(self):
        text = "er: der Fürst"

        result = annotate_text(text, ["er"], tag="em")
        self.assertEqual(result, "<em>er</em>: der Fürst")

        result = annotate_text(text, ["der", "er"], tag="em")
        self.assertEqual(result, "<em>er</em>: <em>der</em> Fürst")

    def test_012_annotate_text_leaves_text_unmodified_when_no_matches(self):
        text = "plain text without matches"

        result = annotate_text(text, [], tag="em")

        self.assertEqual(result, "plain text without matches")

    def test_010_show_tustep(self):
        for x in Beleg.objects.all():
            url = f"/api/show-tustep/{x.dboe_id}"
            response = client.get(url)
            self.assertEqual(response.status_code, 200)
        response = client.get("/api/show-tustep/whatever")
        self.assertEqual(response.status_code, 404)
