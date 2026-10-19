import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.storage.trace_storage import (
    CATEGORY_EXTRACTION_FAILURE,
    CATEGORY_INVALID_JSON,
    CATEGORY_CLASSIFICATION_FAILURE,
    CATEGORY_SUMMARIZATION_FAILURE,
)


class TestPipelineE2E(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.sample_doc = {
            "document_id": "TEST-DOC-101",
            "raw_text": "ABC Technologies invoice dated 12 March 2026 for EUR 5400"
        }

    def test_pipeline_successful_run(self):
        """Tests end-to-end successful pipeline execution and trace persistence."""
        response = self.client.post("/pipeline/intake", json=self.sample_doc)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["message"], "Document processed")
        self.assertEqual(data["document_id"], "TEST-DOC-101")
        self.assertIn("trace_id", data)

        trace = data["trace"]
        self.assertEqual(trace["status"], "success")
        self.assertEqual(len(trace["spans"]), 3)

        # Check all 3 sequential spans
        span_names = [s["step_name"] for s in trace["spans"]]
        self.assertEqual(span_names, ["extraction", "classification", "summarization"])

        for span in trace["spans"]:
            self.assertEqual(span["status"], "success")
            self.assertIsNone(span["error"])
            self.assertGreaterEqual(span["latency_ms"], 0.0)

        trace_id = data["trace_id"]

        # Verify trace retrieval via GET /traces/{trace_id}
        retrieve_res = self.client.get(f"/traces/{trace_id}")
        self.assertEqual(retrieve_res.status_code, 200)
        retrieved_trace = retrieve_res.json()
        self.assertEqual(retrieved_trace["trace_id"], trace_id)
        self.assertEqual(retrieved_trace["status"], "success")

        # Verify SQLite status filtering
        success_traces = self.client.get("/traces?status=success").json()
        trace_ids = [t["trace_id"] for t in success_traces]
        self.assertIn(trace_id, trace_ids)

    def test_pipeline_extraction_failure(self):
        """Tests that extraction failure stops downstream steps and records trace."""
        with patch("backend.app.main.extract_document", side_effect=Exception("Failed to extract invoice metadata")):
            response = self.client.post("/pipeline/intake", json=self.sample_doc)
            self.assertEqual(response.status_code, 200)
            data = response.json()

            self.assertEqual(data["message"], "Extraction failed")
            trace = data["trace"]
            self.assertEqual(trace["status"], "failed")
            self.assertEqual(len(trace["spans"]), 1)
            self.assertEqual(trace["spans"][0]["step_name"], "extraction")
            self.assertEqual(trace["spans"][0]["status"], "failed")

            # Check failure analysis
            analysis_res = self.client.get(f"/traces/{trace['trace_id']}/analysis")
            self.assertEqual(analysis_res.status_code, 200)
            analysis = analysis_res.json()
            self.assertEqual(analysis["failure_category"], CATEGORY_EXTRACTION_FAILURE)

    def test_pipeline_invalid_json_failure(self):
        """Tests that JSON decode errors during extraction are categorized as INVALID_JSON."""
        with patch("backend.app.main.extract_document", side_effect=Exception("JSONDecodeError: Expecting value: line 1 column 1")):
            response = self.client.post("/pipeline/intake", json=self.sample_doc)
            data = response.json()
            trace_id = data["trace_id"]

            analysis_res = self.client.get(f"/traces/{trace_id}/analysis")
            self.assertEqual(analysis_res.status_code, 200)
            analysis = analysis_res.json()
            self.assertEqual(analysis["failure_category"], CATEGORY_INVALID_JSON)

    def test_pipeline_classification_failure(self):
        """Tests that classification failure stops summarization and records trace."""
        with patch("backend.app.main.classify_document", side_effect=Exception("Classifier timeout")):
            response = self.client.post("/pipeline/intake", json=self.sample_doc)
            self.assertEqual(response.status_code, 200)
            data = response.json()

            self.assertEqual(data["message"], "Classification failed")
            trace = data["trace"]
            self.assertEqual(trace["status"], "failed")
            # Extraction succeeded, classification failed, summarization not run
            self.assertEqual(len(trace["spans"]), 2)
            self.assertEqual(trace["spans"][0]["status"], "success")
            self.assertEqual(trace["spans"][1]["step_name"], "classification")
            self.assertEqual(trace["spans"][1]["status"], "failed")

            # Check failure analysis
            analysis_res = self.client.get(f"/traces/{trace['trace_id']}/analysis")
            self.assertEqual(analysis_res.status_code, 200)
            analysis = analysis_res.json()
            self.assertEqual(analysis["failure_category"], CATEGORY_CLASSIFICATION_FAILURE)

    def test_pipeline_summarization_failure(self):
        """Tests that summarization failure records all 3 spans with last one failed."""
        with patch("backend.app.main.summarize_document", side_effect=Exception("Summary generation failed")):
            response = self.client.post("/pipeline/intake", json=self.sample_doc)
            self.assertEqual(response.status_code, 200)
            data = response.json()

            self.assertEqual(data["message"], "Summarization failed")
            trace = data["trace"]
            self.assertEqual(trace["status"], "failed")
            self.assertEqual(len(trace["spans"]), 3)
            self.assertEqual(trace["spans"][0]["status"], "success")
            self.assertEqual(trace["spans"][1]["status"], "success")
            self.assertEqual(trace["spans"][2]["step_name"], "summarization")
            self.assertEqual(trace["spans"][2]["status"], "failed")

            # Check failure analysis
            analysis_res = self.client.get(f"/traces/{trace['trace_id']}/analysis")
            self.assertEqual(analysis_res.status_code, 200)
            analysis = analysis_res.json()
            self.assertEqual(analysis["failure_category"], CATEGORY_SUMMARIZATION_FAILURE)

    def test_nonexistent_trace_returns_404(self):
        """Tests 404 handling for invalid/missing trace IDs."""
        res_trace = self.client.get("/traces/does-not-exist")
        self.assertEqual(res_trace.status_code, 404)

        res_analysis = self.client.get("/traces/does-not-exist/analysis")
        self.assertEqual(res_analysis.status_code, 404)


if __name__ == "__main__":
    unittest.main()
