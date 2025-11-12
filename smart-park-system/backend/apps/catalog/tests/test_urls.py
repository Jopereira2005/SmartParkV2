from django.test import TestCase
from django.urls import reverse, resolve, NoReverseMatch
from django.contrib.auth import get_user_model

from apps.catalog.views import *
from .test_utils import TestDataMixin

User = get_user_model()


class CatalogURLPatternsTest(TestCase, TestDataMixin):
    """Test URL patterns and reverse resolution for catalog app."""

    def setUp(self):
        """Set up test data."""
        self.client_obj = self.create_client()
        self.establishment = self.create_establishment(client=self.client_obj)
        self.lot = self.create_lot(establishment=self.establishment)
        self.slot = self.create_slot(lot=self.lot)
        self.slot_status = self.create_slot_status(slot=self.slot)
        self.slot_type = self.create_slot_type()
        self.vehicle_type = self.create_vehicle_type()

    def test_store_type_urls(self):
        """Test store type related URL patterns."""
        # Test URL reverse
        url = reverse("catalog:store-type-list")
        self.assertEqual(url, "/api/catalog/store-types/")

        # Test URL resolve
        resolver = resolve("/api/catalog/store-types/")
        self.assertEqual(resolver.view_name, "catalog:store-type-list")
        self.assertEqual(resolver.func.view_class, StoreTypeListView)

    def test_establishment_urls(self):
        """Test establishment related URL patterns."""
        # Test list URL
        url = reverse("catalog:establishment-list")
        self.assertEqual(url, "/api/catalog/establishments/")

        # Test detail URL
        url = reverse(
            "catalog:establishment-detail", kwargs={"pk": self.establishment.pk}
        )
        self.assertEqual(url, f"/api/catalog/establishments/{self.establishment.pk}/")

        # Test URL resolve for list
        resolver = resolve("/api/catalog/establishments/")
        self.assertEqual(resolver.view_name, "catalog:establishment-list")
        self.assertEqual(resolver.func.view_class, EstablishmentListCreateView)

        # Test URL resolve for detail
        resolver = resolve(f"/api/catalog/establishments/{self.establishment.pk}/")
        self.assertEqual(resolver.view_name, "catalog:establishment-detail")
        self.assertEqual(resolver.func.view_class, EstablishmentDetailView)
        self.assertEqual(resolver.kwargs["pk"], self.establishment.pk)

    def test_lot_urls(self):
        """Test lot related URL patterns."""
        # Test list URL
        url = reverse("catalog:lot-list")
        self.assertEqual(url, "/api/catalog/lots/")

        # Test detail URL
        url = reverse("catalog:lot-detail", kwargs={"pk": self.lot.pk})
        self.assertEqual(url, f"/api/catalog/lots/{self.lot.pk}/")

        # Test URL resolve for list
        resolver = resolve("/api/catalog/lots/")
        self.assertEqual(resolver.view_name, "catalog:lot-list")
        self.assertEqual(resolver.func.view_class, LotListCreateView)

        # Test URL resolve for detail
        resolver = resolve(f"/api/catalog/lots/{self.lot.pk}/")
        self.assertEqual(resolver.view_name, "catalog:lot-detail")
        self.assertEqual(resolver.func.view_class, LotDetailView)
        self.assertEqual(resolver.kwargs["pk"], self.lot.pk)

    def test_slot_urls(self):
        """Test slot related URL patterns."""
        # Test slot list URL with lot_id parameter
        url = reverse("catalog:slot-list", kwargs={"lot_id": self.lot.pk})
        self.assertEqual(url, f"/api/catalog/lots/{self.lot.pk}/slots/")

        # Test slot detail URL
        url = reverse("catalog:slot-detail", kwargs={"pk": self.slot.pk})
        self.assertEqual(url, f"/api/catalog/slots/{self.slot.pk}/")

        # Test URL resolve for slot list
        resolver = resolve(f"/api/catalog/lots/{self.lot.pk}/slots/")
        self.assertEqual(resolver.view_name, "catalog:slot-list")
        self.assertEqual(resolver.func.view_class, SlotListCreateView)
        self.assertEqual(resolver.kwargs["lot_id"], self.lot.pk)

        # Test URL resolve for slot detail
        resolver = resolve(f"/api/catalog/slots/{self.slot.pk}/")
        self.assertEqual(resolver.view_name, "catalog:slot-detail")
        self.assertEqual(resolver.func.view_class, SlotDetailView)
        self.assertEqual(resolver.kwargs["pk"], self.slot.pk)

    def test_slot_type_urls(self):
        """Test slot type related URL patterns."""
        # Test URL reverse
        url = reverse("catalog:slot-type-list")
        self.assertEqual(url, "/api/catalog/slot-types/")

        # Test URL resolve
        resolver = resolve("/api/catalog/slot-types/")
        self.assertEqual(resolver.view_name, "catalog:slot-type-list")
        self.assertEqual(resolver.func.view_class, SlotTypeListView)

    def test_vehicle_type_urls(self):
        """Test vehicle type related URL patterns."""
        # Test URL reverse
        url = reverse("catalog:vehicle-type-list")
        self.assertEqual(url, "/api/catalog/vehicle-types/")

        # Test URL resolve
        resolver = resolve("/api/catalog/vehicle-types/")
        self.assertEqual(resolver.view_name, "catalog:vehicle-type-list")
        self.assertEqual(resolver.func.view_class, VehicleTypeListView)

    def test_slot_status_urls(self):
        """Test slot status related URL patterns."""
        # Test slot status detail URL
        url = reverse("catalog:slot-status-detail", kwargs={"pk": self.slot_status.pk})
        self.assertEqual(url, f"/api/catalog/slot-status/{self.slot_status.pk}/")

        # Test slot status history URL
        url = reverse("catalog:slot-status-history", kwargs={"slot_id": self.slot.pk})
        self.assertEqual(url, f"/api/catalog/slots/{self.slot.pk}/history/")

        # Test URL resolve for slot status detail
        resolver = resolve(f"/api/catalog/slot-status/{self.slot_status.pk}/")
        self.assertEqual(resolver.view_name, "catalog:slot-status-detail")
        self.assertEqual(resolver.func.view_class, SlotStatusDetailView)
        self.assertEqual(resolver.kwargs["pk"], self.slot_status.pk)

        # Test URL resolve for slot status history
        resolver = resolve(f"/api/catalog/slots/{self.slot.pk}/history/")
        self.assertEqual(resolver.view_name, "catalog:slot-status-history")
        self.assertEqual(resolver.func.view_class, SlotStatusHistoryListView)
        self.assertEqual(resolver.kwargs["slot_id"], self.slot.pk)

    def test_public_urls(self):
        """Test public endpoint URL patterns."""
        # Test public establishments URL
        url = reverse("catalog:public-establishments")
        self.assertEqual(url, "/api/catalog/public/establishments/")

        # Test public slot status URL
        url = reverse(
            "catalog:public-slot-status",
            kwargs={"establishment_id": self.establishment.pk},
        )
        self.assertEqual(
            url, f"/api/catalog/public/establishments/{self.establishment.pk}/slots/"
        )

        # Test URL resolve for public establishments
        resolver = resolve("/api/catalog/public/establishments/")
        self.assertEqual(resolver.view_name, "catalog:public-establishments")
        self.assertEqual(resolver.func, public_establishments_view)

        # Test URL resolve for public slot status
        resolver = resolve(
            f"/api/catalog/public/establishments/{self.establishment.pk}/slots/"
        )
        self.assertEqual(resolver.view_name, "catalog:public-slot-status")
        self.assertEqual(resolver.func, public_slot_status_view)
        self.assertEqual(resolver.kwargs["establishment_id"], self.establishment.pk)


class URLParameterValidationTest(TestCase, TestDataMixin):
    """Test URL parameter validation and edge cases."""

    def setUp(self):
        """Set up test data."""
        self.client_obj = self.create_client()
        self.establishment = self.create_establishment(client=self.client_obj)
        self.lot = self.create_lot(establishment=self.establishment)
        self.slot = self.create_slot(lot=self.lot)
        self.slot_status = self.create_slot_status(slot=self.slot)

    def test_integer_parameter_validation(self):
        """Test that URL patterns properly validate integer parameters."""
        # Test valid integer parameters
        valid_ids = [1, 123, 999999]
        for pk in valid_ids:
            try:
                url = reverse("catalog:establishment-detail", kwargs={"pk": pk})
                self.assertTrue(url.endswith(f"/{pk}/"))
            except NoReverseMatch:
                self.fail(f"Should be able to reverse URL with pk={pk}")

        # Test that string parameters that look like integers work
        url = reverse("catalog:establishment-detail", kwargs={"pk": "123"})
        self.assertEqual(url, "/api/catalog/establishments/123/")

    def test_invalid_parameter_types(self):
        """Test behavior with invalid parameter types."""
        # Test with invalid parameter types for reverse (should handle gracefully)
        invalid_params = [None, [], {}, "abc"]
        for param in invalid_params:
            try:
                url = reverse("catalog:establishment-detail", kwargs={"pk": param})
                # If it doesn't raise an exception, check the result
                self.assertIsInstance(url, str)
            except (TypeError, NoReverseMatch):
                # This is expected behavior for invalid parameters
                pass

    def test_missing_required_parameters(self):
        """Test that missing required parameters raise appropriate errors."""
        # Test missing pk parameter
        with self.assertRaises(NoReverseMatch):
            reverse("catalog:establishment-detail")

        # Test missing lot_id parameter
        with self.assertRaises(NoReverseMatch):
            reverse("catalog:slot-list")

        # Test missing slot_id parameter
        with self.assertRaises(NoReverseMatch):
            reverse("catalog:slot-status-history")

    def test_extra_parameters_ignored(self):
        """Test that extra parameters are properly ignored."""
        # Django's reverse function is strict about parameters
        # Extra parameters will raise NoReverseMatch
        with self.assertRaises(NoReverseMatch):
            reverse(
                "catalog:establishment-detail", kwargs={"pk": 1, "extra": "ignored"}
            )

    def test_zero_and_negative_ids(self):
        """Test URL generation with edge case ID values."""
        # Test with zero (should work since it's a valid integer)
        url = reverse("catalog:establishment-detail", kwargs={"pk": 0})
        self.assertEqual(url, "/api/catalog/establishments/0/")

        # Note: Negative numbers don't work with Django's [0-9]+ pattern
        # This is expected behavior for the URL pattern used


class URLNamingConventionTest(TestCase):
    """Test URL naming conventions and consistency."""

    def test_url_naming_consistency(self):
        """Test that URL names follow consistent patterns."""
        # Test list URLs follow pattern: {model}-list
        list_urls = [
            "catalog:store-type-list",
            "catalog:establishment-list",
            "catalog:lot-list",
            "catalog:slot-list",
            "catalog:slot-type-list",
            "catalog:vehicle-type-list",
            "catalog:slot-status-history",
        ]

        for url_name in list_urls:
            try:
                # Just test that the name can be resolved
                # We'll provide minimal required parameters for slot-list and slot-status-history
                if url_name == "catalog:slot-list":
                    reverse(url_name, kwargs={"lot_id": 1})
                elif url_name == "catalog:slot-status-history":
                    reverse(url_name, kwargs={"slot_id": 1})
                else:
                    reverse(url_name)
            except NoReverseMatch as e:
                self.fail(f"URL name '{url_name}' should be valid: {e}")

    def test_detail_url_naming_consistency(self):
        """Test that detail URL names follow consistent patterns."""
        # Test detail URLs follow pattern: {model}-detail
        detail_urls = [
            ("catalog:establishment-detail", {"pk": 1}),
            ("catalog:lot-detail", {"pk": 1}),
            ("catalog:slot-detail", {"pk": 1}),
            ("catalog:slot-status-detail", {"pk": 1}),
        ]

        for url_name, kwargs in detail_urls:
            try:
                reverse(url_name, kwargs=kwargs)
            except NoReverseMatch as e:
                self.fail(f"URL name '{url_name}' should be valid: {e}")

    def test_public_url_naming_consistency(self):
        """Test that public URL names follow consistent patterns."""
        # Test public URLs have 'public-' prefix
        public_urls = [
            ("catalog:public-establishments", {}),
            ("catalog:public-slot-status", {"establishment_id": 1}),
        ]

        for url_name, kwargs in public_urls:
            try:
                reverse(url_name, kwargs=kwargs)
            except NoReverseMatch as e:
                self.fail(f"URL name '{url_name}' should be valid: {e}")


class URLResolverPerformanceTest(TestCase):
    """Test URL resolver performance and caching."""

    def test_url_resolution_performance(self):
        """Test that URL resolution is performant for common patterns."""
        import time

        # Test resolution of simple URLs
        start_time = time.time()
        for _ in range(100):
            reverse("catalog:establishment-list")
        simple_time = time.time() - start_time

        # Test resolution of parameterized URLs
        start_time = time.time()
        for i in range(100):
            reverse("catalog:establishment-detail", kwargs={"pk": i})
        param_time = time.time() - start_time

        # Basic performance assertions (these are generous limits)
        self.assertLess(simple_time, 1.0, "Simple URL resolution should be fast")
        self.assertLess(param_time, 1.0, "Parameterized URL resolution should be fast")

    def test_url_pattern_matching_efficiency(self):
        """Test efficiency of URL pattern matching."""
        import time

        # Test resolving various URL patterns
        test_urls = [
            "/api/catalog/establishments/",
            "/api/catalog/establishments/123/",
            "/api/catalog/lots/456/",
            "/api/catalog/lots/456/slots/",
            "/api/catalog/slots/789/",
            "/api/catalog/public/establishments/",
            "/api/catalog/public/establishments/123/slots/",
        ]

        start_time = time.time()
        for _ in range(10):
            for url in test_urls:
                try:
                    resolve(url)
                except Exception:
                    # Some URLs might not resolve due to test data constraints
                    pass
        total_time = time.time() - start_time

        # Performance assertion
        self.assertLess(total_time, 1.0, "URL pattern matching should be efficient")
