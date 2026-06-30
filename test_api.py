import os
import unittest

# Set DEMO_MODE=True before imports to ensure mock fallbacks are used during test suite execution
os.environ["DEMO_MODE"] = "True"

from fastapi.testclient import TestClient
from main import app

class TestEduGenieAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize database
        import database
        database.init_db()
        # Create TestClient instance
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        # Clean up database file after tests
        import os
        if os.path.exists("edugenie.db"):
            try:
                os.remove("edugenie.db")
            except Exception:
                pass

    def test_health_check(self):
        """
        Tests that /health returns status 200 and healthy status.
        """
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy"})

    def test_serve_index(self):
        """
        Tests that / renders index.html.
        """
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_qa_endpoint(self):
        """
        Tests educational Q&A endpoint returns question and answer keys.
        """
        response = self.client.get("/qa?question=What is photosynthesis?")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("question", data)
        self.assertIn("answer", data)
        self.assertEqual(data["question"], "What is photosynthesis?")
        self.assertTrue(len(data["answer"]) > 0)

    def test_qa_validation_error(self):
        """
        Tests that short inputs trigger validation errors on the QA endpoint.
        """
        response = self.client.get("/qa?question=ab")
        self.assertEqual(response.status_code, 422)

    def test_explain_endpoint(self):
        """
        Tests concept explanation POST endpoint with proper body.
        """
        response = self.client.post("/explain", json={"topic": "Gravity"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("topic", data)
        self.assertIn("explanation", data)
        self.assertEqual(data["topic"], "Gravity")
        self.assertTrue(len(data["explanation"]) > 0)

    def test_explain_validation_error(self):
        """
        Tests that empty topic string triggers validation error.
        """
        response = self.client.post("/explain", json={"topic": ""})
        self.assertEqual(response.status_code, 422)

    def test_summarize_endpoint(self):
        """
        Tests text summarization POST endpoint with valid body.
        """
        text = "Photosynthesis is a process used by plants and other organisms to convert light energy into chemical energy."
        response = self.client.post("/summarize", json={"text": text})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("summary", data)
        self.assertTrue(len(data["summary"]) > 0)

    def test_quiz_endpoint(self):
        """
        Tests quiz generation endpoint. Verifies exactly 3 MCQs,
        each with 4 options, and correct_answer inside the options.
        """
        response = self.client.post("/quiz", json={"topic": "Binary Search"})
        self.assertEqual(response.status_code, 200)
        questions = response.json()
        self.assertIsInstance(questions, list)
        self.assertEqual(len(questions), 3)
        for idx, q in enumerate(questions):
            self.assertIn("question", q)
            self.assertIn("options", q)
            self.assertIn("correct_answer", q)
            self.assertEqual(len(q["options"]), 4)
            self.assertIn(q["correct_answer"], q["options"])

    def test_learning_recommendations_endpoint(self):
        """
        Tests learning path recommendation GET endpoint.
        """
        response = self.client.get("/learn/recommendations?topic=Quantum Mechanics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("topic", data)
        self.assertIn("roadmap", data)
        self.assertEqual(data["topic"], "Quantum Mechanics")
        self.assertTrue(len(data["roadmap"]) > 0)

if __name__ == "__main__":
    unittest.main()
