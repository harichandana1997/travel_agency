import unittest
from unittest.mock import Mock, patch

from src import (
    DEFAULT_PREFERENCES,
    apply_chat_preference,
    build_itinerary,
    estimate_bus_options,
    get_road_route,
    get_routes,
    rank_routes,
)
from src.llm import langchain_is_configured


class PlannerTests(unittest.TestCase):
    def test_lowest_fare_ranks_first_by_default(self) -> None:
        preferences = {**DEFAULT_PREFERENCES, "comfort": []}
        routes = rank_routes(get_routes("Delhi", "Jaipur"), preferences)
        self.assertEqual(routes[0].fare_inr, 390)

    def test_budget_and_comfort_filter_routes(self) -> None:
        preferences = {
            **DEFAULT_PREFERENCES,
            "budget_inr": 700,
            "comfort": ["AC", "Sleeper"],
        }
        routes = rank_routes(get_routes("Delhi", "Jaipur"), preferences)
        self.assertEqual([route.operator for route in routes], ["Rajasthan Roadlines"])

    def test_unknown_city_pair_has_no_sample_routes(self) -> None:
        self.assertEqual(get_routes("Jaipur", "Delhi"), [])

    def test_road_route_geocodes_arbitrary_places_and_returns_path(self) -> None:
        geocode_response = Mock()
        geocode_response.raise_for_status.return_value = None
        geocode_response.json.side_effect = [
            [{"lon": "77.5946", "lat": "12.9716"}],
            [{"lon": "78.4867", "lat": "17.3850"}],
        ]
        road_response = Mock()
        road_response.raise_for_status.return_value = None
        road_response.json.return_value = {
            "code": "Ok",
            "routes": [
                {
                    "distance": 570000,
                    "duration": 36000,
                    "geometry": {"coordinates": [[77.5946, 12.9716], [78.4867, 17.385]]},
                }
            ],
        }
        with patch("src.route.requests.get", side_effect=[geocode_response, geocode_response, road_response]):
            route = get_road_route("Bengaluru", "Hyderabad")
        self.assertEqual(route.distance_km, 570)
        self.assertEqual(route.duration_text, "10h 00m")
        self.assertEqual(len(route.coordinates), 2)

    def test_road_route_rejects_empty_city_name(self) -> None:
        with self.assertRaisesRegex(ValueError, "both an origin and a destination"):
            get_road_route("", "Hyderabad")

    def test_bus_estimates_are_available_for_arbitrary_route_distance(self) -> None:
        from src import RoadRouteEstimate

        route = RoadRouteEstimate(
            origin="Nellore",
            destination="Bengaluru",
            distance_km=400,
            duration_minutes=360,
            coordinates=((79.98, 14.44), (77.59, 12.97)),
        )
        options = estimate_bus_options(route, DEFAULT_PREFERENCES)
        self.assertEqual([option["bus_type"] for option in options], ["AC Seater", "AC Sleeper"])
        self.assertEqual((options[0]["fare_min"], options[0]["fare_max"]), (480, 880))
        self.assertLess(options[0]["duration_min"], options[0]["duration_max"])

    def test_bus_estimates_respect_selected_comfort_and_budget(self) -> None:
        from src import RoadRouteEstimate

        route = RoadRouteEstimate(
            origin="Nellore",
            destination="Bengaluru",
            distance_km=400,
            duration_minutes=360,
            coordinates=(),
        )
        preferences = {**DEFAULT_PREFERENCES, "comfort": ["Sleeper"], "budget_inr": 700}
        self.assertEqual(estimate_bus_options(route, preferences), [])

    def test_chat_can_update_budget_and_bus_type(self) -> None:
        update = apply_chat_preference("Please keep it under ₹900 and prefer sleeper", {})
        self.assertEqual(update["budget_inr"], 900)
        self.assertIn("Sleeper", update["comfort"])

    def test_itinerary_has_flexible_day_parts(self) -> None:
        itinerary = build_itinerary("Delhi", "Jaipur")
        self.assertEqual([stop["time"] for stop in itinerary], ["Morning", "Lunch", "Afternoon"])

    def test_groq_key_controls_langchain_configuration(self) -> None:
        with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}, clear=True):
            self.assertTrue(langchain_is_configured())
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=True):
            self.assertFalse(langchain_is_configured())


if __name__ == "__main__":
    unittest.main()
