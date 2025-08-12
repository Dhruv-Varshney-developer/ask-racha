from typing import List, Dict, Optional
import os
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.http import models
from llama_index.core import Document
import uuid


class VectorStore:
    """Vector database interface for storing and querying document embeddings."""

    DEFAULT_LOCAL_PORT = 6343
    DEFAULT_CLOUD_PORT = 6333

    def __init__(self, is_local: bool = True):
        """Initialize vector store with local or cloud configuration."""
        self.is_local = is_local
        self.host = "localhost" if is_local else os.getenv("QDRANT_HOST")
        self.api_key = None if is_local else os.getenv("QDRANT_API_KEY")
        self.port = int(
            os.getenv(
                "QDRANT_PORT",
                self.DEFAULT_LOCAL_PORT if is_local else self.DEFAULT_CLOUD_PORT,
            )
        )

        if not self.host and not is_local:
            raise ValueError("QDRANT_HOST not found in environment variables")

        self.client = QdrantClient(host=self.host, port=self.port, api_key=self.api_key)

        self.collection_name = "askracha-docs"
        self.dimension = 768

    def initialize_index(self) -> Dict:
        """Create collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)

            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.dimension, distance=models.Distance.COSINE
                    ),
                )
                return {
                    "success": True,
                    "message": f"Collection {self.collection_name} created successfully",
                }
            return {
                "success": True,
                "message": f"Collection {self.collection_name} already exists",
            }
        except Exception as e:
            return {"success": False, "message": f"Error creating collection: {str(e)}"}

    def upsert_documents(self, documents: List[Document]) -> Dict:
        """Insert or update documents with their embeddings and metadata."""
        try:
            current_time = int(datetime.now().timestamp())
            points = []
            vector_ids = []

            for doc in documents:
                vector_id = doc.doc_id or str(uuid.uuid4())
                vector_ids.append(vector_id)

                if not hasattr(doc, "embedding"):
                    return {"success": False, "message": "Document missing embedding"}

                points.append(
                    models.PointStruct(
                        id=vector_id,
                        vector=doc.embedding,
                        payload={
                            **doc.metadata,
                            "timestamp": current_time,
                            "text": doc.text[:1000],
                        },
                    )
                )

            self.client.upsert(collection_name=self.collection_name, points=points)

            return {
                "success": True,
                "message": f"Successfully upserted {len(points)} documents",
                "count": len(points),
                "ids": vector_ids,
            }
        except Exception as e:
            return {"success": False, "message": f"Error upserting documents: {str(e)}"}

    def delete_documents(self, ids: List[str]) -> Dict:
        """Delete documents by their unique IDs."""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=ids),
            )
            return {"success": True, "message": "Documents deleted successfully"}
        except Exception as e:
            return {"success": False, "message": f"Error deleting documents: {str(e)}"}

    def cleanup_old_vectors(self, before_timestamp: int) -> Dict:
        """Delete vectors older than specified timestamp."""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="timestamp",
                                match=models.MatchValue(value=before_timestamp),
                                range=models.Range(lt=before_timestamp),
                            )
                        ]
                    )
                ),
            )
            return {
                "success": True,
                "message": f"Successfully cleaned up vectors before timestamp {before_timestamp}",
            }
        except Exception as e:
            return {"success": False, "message": f"Error cleaning up vectors: {str(e)}"}

    def get_stats(self) -> Dict:
        """Get collection statistics including vector and point counts."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "success": True,
                "stats": type(
                    "Stats",
                    (),
                    {
                        "vectors_count": info.vectors_count or 0,
                        "points_count": info.points_count or 0,
                        "segments_count": info.segments_count or 0,
                        "status": info.status,
                    },
                )(),
            }
        except Exception as e:
            return {"success": False, "message": f"Error getting stats: {str(e)}"}
