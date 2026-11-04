import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src import delete_saved_trip, list_saved_trips, load_memory, save_preferences, save_trip


class LocalMemoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "memory.sqlite3"
        self.environment = patch.dict(
            "os.environ",
            {"SUPABASE_URL": "", "SUPABASE_SECRET_KEY": ""},
        )
        self.environment.start()
        self.database = patch("src.memory._database_path", return_value=self.database_path)
        self.database.start()

    def tearDown(self) -> None:
        self.database.stop()
        self.environment.stop()
        self.temp_dir.cleanup()

    def test_preferences_round_trip_in_local_database(self) -> None:
        preferences = {"budget_inr": 1200, "comfort": ["AC", "Sleeper"]}
        save_preferences(preferences, "Prefers sleeper buses")
        self.assertEqual(
            load_memory(),
            {"summary": "Prefers sleeper buses", "preferences": preferences},
        )

    def test_saved_trips_can_be_listed_and_deleted(self) -> None:
        trip_id = save_trip(
            "Nellore",
            "Bengaluru",
            "2026-11-07",
            {"comfort": ["AC"]},
            [{"time": "Morning", "title": "Explore", "description": "Take it easy."}],
        )
        trips = list_saved_trips()
        self.assertEqual(len(trips), 1)
        self.assertEqual(trips[0]["id"], trip_id)
        self.assertEqual(trips[0]["origin"], "Nellore")
        self.assertEqual(trips[0]["itinerary"][0]["title"], "Explore")

        delete_saved_trip(trip_id)
        self.assertEqual(list_saved_trips(), [])

    def test_partial_supabase_configuration_is_reported(self) -> None:
        with patch.dict(
            "os.environ",
            {"SUPABASE_URL": "https://example.supabase.co", "SUPABASE_SECRET_KEY": ""},
        ):
            with self.assertRaisesRegex(RuntimeError, "partially configured"):
                load_memory()


if __name__ == "__main__":
    unittest.main()
