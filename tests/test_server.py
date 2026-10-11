import json
import unittest
from unittest.mock import patch

import server


class ValidateInputTests(unittest.TestCase):
    def test_validates_and_trims_garden_details(self):
        result = server.validate_input({
            "location": "  Portland, Oregon ",
            "last_frost_date": "2027-04-15",
            "plants": "  tomatoes, basil  ",
        })
        self.assertEqual(result["location"], "Portland, Oregon")
        self.assertEqual(result["plants"], "tomatoes, basil")
        self.assertEqual(result["last_frost_date"], "2027-04-15")

    def test_rejects_invalid_date(self):
        with self.assertRaisesRegex(ValueError, "valid last frost date"):
            server.validate_input({"last_frost_date": "not-a-date", "plants": "beans"})

    def test_rejects_missing_plants(self):
        with self.assertRaisesRegex(ValueError, "List at least one plant"):
            server.validate_input({"last_frost_date": "2027-04-15", "plants": " "})


class GeneratePlanTests(unittest.TestCase):
    @patch("server.urlopen")
    def test_uses_local_model_and_returns_structured_plan(self, mock_urlopen):
        expected = {
            "headline": "Start with a sunny spot",
            "planting_window": "Wait until after your estimated frost date.",
            "outdoor_plan": [{
                "title": "Find a sunny patch",
                "duration_minutes": 15,
                "instructions": "Notice where sunlight lands in your garden.",
            }],
            "notes": "Frost dates are estimates; check local conditions before planting.",
        }
        response_data = json.dumps({"message": {"content": json.dumps(expected)}}).encode()
        response = mock_urlopen.return_value.__enter__.return_value
        response.read.return_value = response_data

        result = server.generate_plan({
            "location": "",
            "last_frost_date": "2027-04-15",
            "plants": "tomatoes",
        })

        self.assertEqual(result, expected)
        request = mock_urlopen.call_args.args[0]
        self.assertTrue(request.full_url.endswith("/api/chat"))
        sent = json.loads(request.data)
        self.assertEqual(sent["model"], server.MODEL)
        self.assertEqual(sent["stream"], False)

    @patch("server.urlopen", side_effect=server.URLError("offline"))
    def test_reports_when_local_model_is_unavailable(self, _mock_urlopen):
        with self.assertRaisesRegex(server.LocalModelError, "Can't reach Ollama"):
            server.generate_plan({
                "location": "",
                "last_frost_date": "2027-04-15",
                "plants": "tomatoes",
            })

    def test_rejects_model_activity_with_out_of_range_duration(self):
        plan = {
            "headline": "Grow tomatoes",
            "planting_window": "After frost",
            "outdoor_plan": [{
                "title": "Plant",
                "duration_minutes": 0,
                "instructions": "Plant the seeds.",
            }],
            "notes": "Check your local conditions.",
        }
        with self.assertRaisesRegex(server.LocalModelError, "invalid activity duration"):
            server.validate_plan(plan)


if __name__ == "__main__":
    unittest.main()
