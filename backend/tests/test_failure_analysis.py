import unittest
from backend.app.storage.trace_storage import (
    categorize_failure,
    analyze_failure,
    CATEGORY_EXTRACTION_FAILURE,
    CATEGORY_INVALID_JSON,
    CATEGORY_CLASSIFICATION_FAILURE,
    CATEGORY_SUMMARIZATION_FAILURE,
    CATEGORY_UNKNOWN_ERROR,
)


class TestFailureCategories(unittest.TestCase):
    def test_invalid_json_category(self):
        # JSON error in extraction or any step should classify as INVALID_JSON
        self.assertEqual(
            categorize_failure("extraction", "JSONDecodeError: Expecting value: line 1 column 1 (char 0)"),
            CATEGORY_INVALID_JSON,
        )
        self.assertEqual(
            categorize_failure("extraction", "Invalid json payload received"),
            CATEGORY_INVALID_JSON,
        )

    def test_extraction_failure_category(self):
        # General extraction failures (not JSON)
        self.assertEqual(
            categorize_failure("extraction", "Simulated extraction failure"),
            CATEGORY_EXTRACTION_FAILURE,
        )
        self.assertEqual(
            categorize_failure("extraction", "KeyError: 'amount' not found in document"),
            CATEGORY_EXTRACTION_FAILURE,
        )

    def test_classification_failure_category(self):
        self.assertEqual(
            categorize_failure("classification", "Invalid category returned by classifier"),
            CATEGORY_CLASSIFICATION_FAILURE,
        )

    def test_summarization_failure_category(self):
        self.assertEqual(
            categorize_failure("summarization", "Text exceeds maximum summary length"),
            CATEGORY_SUMMARIZATION_FAILURE,
        )

    def test_unknown_error_category(self):
        # Unrecognized step or generic system errors
        self.assertEqual(
            categorize_failure("database_sync", "Connection refused"),
            CATEGORY_UNKNOWN_ERROR,
        )
        self.assertEqual(
            categorize_failure(None, None),
            CATEGORY_UNKNOWN_ERROR,
        )
        self.assertEqual(
            categorize_failure("", ""),
            CATEGORY_UNKNOWN_ERROR,
        )

    def test_analyze_failure_on_existing_trace(self):
        # Test on the known failed trace ID in backend/app/storage/traces
        result = analyze_failure("511386ac-43df-478f-a7be-a91beb402357")
        self.assertIsNotNone(result)
        self.assertEqual(result["trace_id"], "511386ac-43df-478f-a7be-a91beb402357")
        self.assertEqual(result["trace_status"], "failed")
        self.assertEqual(result["failure_count"], 1)
        self.assertEqual(result["failure_category"], CATEGORY_EXTRACTION_FAILURE)

        failure_item = result["failures"][0]
        self.assertEqual(failure_item["step_name"], "extraction")
        self.assertEqual(failure_item["failure_category"], CATEGORY_EXTRACTION_FAILURE)
        self.assertIn("Simulated extraction failure", failure_item["error"])
        self.assertIn("deliberately failed", failure_item["likely_cause"])
        self.assertIn("Remove the temporary test exception", failure_item["recommended_action"])

    def test_analyze_failure_nonexistent_trace(self):
        # Should return None when trace does not exist
        result = analyze_failure("non-existent-trace-id")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
