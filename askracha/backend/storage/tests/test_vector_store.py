import unittest
from datetime import datetime, timedelta
from llama_index.core import Document
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from storage.vector_store import VectorStore


class TestVectorStore(unittest.TestCase):
    def setUp(self):
        self.store = VectorStore(is_local=True)
        init_result = self.store.initialize_index()
        self.assertTrue(init_result["success"])

    def test_upsert_and_delete(self):
        docs = [
            Document(
                text="Test document 1",
                metadata={"source": "test1.txt"},
                embedding=[0.1] * 768,
            ),
            Document(
                text="Test document 2",
                metadata={"source": "test2.txt"},
                embedding=[0.2] * 768,
            ),
        ]

        result = self.store.upsert_documents(docs)
        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 2)
        self.assertEqual(len(result["ids"]), 2)

        stats = self.store.get_stats()
        self.assertTrue(stats["success"])
        self.assertGreaterEqual(stats["stats"].points_count, 2)

        delete_result = self.store.delete_documents([result["ids"][0]])
        self.assertTrue(delete_result["success"])

    def test_cleanup_old_vectors(self):
        doc = Document(
            text="Test document",
            metadata={"source": "cleanup_test.txt"},
            embedding=[0.1] * 768,
        )

        result = self.store.upsert_documents([doc])
        self.assertTrue(result["success"])

        future_time = int((datetime.now() + timedelta(days=1)).timestamp())
        result = self.store.cleanup_old_vectors(future_time)
        self.assertTrue(result["success"])


if __name__ == "__main__":
    unittest.main()
