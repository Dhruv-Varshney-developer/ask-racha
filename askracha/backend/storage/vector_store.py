from typing import List, Dict, Optional
import os
import hashlib
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.http import models
from llama_index.core import Document
from llama_index.embeddings.gemini import GeminiEmbedding
import uuid


class VectorStore:
    """Vector database interface for storing and querying document embeddings."""

    DEFAULT_LOCAL_PORT = 6343
    DEFAULT_CLOUD_PORT = 6333

    def __init__(self, is_local: bool = True):
        """Initialize vector store with local or cloud configuration."""
        self.is_local = is_local
        env_host = os.getenv("QDRANT_HOST")
        env_port = os.getenv("QDRANT_PORT")
        self.host = env_host if env_host else ("localhost" if is_local else os.getenv("QDRANT_HOST"))
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

        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            self._embed_model = GeminiEmbedding(
                model_name="models/text-embedding-004", api_key=api_key
            )
        else:
            self._embed_model = None

        self._ensure_payload_indexes()

    def _ensure_payload_indexes(self):
        """Ensure payload indexes exist for efficient duplicate checking."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)

            if exists:
                try:
                    self.client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name="content_hash",
                        field_schema=models.PayloadFieldSchema.KEYWORD,
                    )
                except Exception:
                    # Index might already exist, ignoring error
                    pass
        except Exception:
            pass

    def _generate_content_hash(self, text: str, source: str) -> str:
        """Generate a unique hash for document content and source."""
        content = f"{source}:{text[:1000]}"  # Using first 1000 chars + source
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def _find_existing_document(self, content_hash: str) -> Optional[str]:
        """Find existing document by content hash."""
        try:
            result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="content_hash",
                            match=models.MatchValue(value=content_hash),
                        )
                    ]
                ),
                limit=1,
                with_payload=False,
            )

            if result[0]:
                return result[0][0].id
            return None
        except Exception:
            return None

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

                try:
                    self.client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name="content_hash",
                        field_schema=models.PayloadFieldSchema.KEYWORD,
                    )
                except Exception as e:
                    print(f"Warning: Failed to create content_hash index: {e}")

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
        """Insert or update documents with deduplication."""
        try:
            current_time = int(datetime.now().timestamp())
            points_to_insert = []
            points_to_update = []
            vector_ids = []
            duplicates_found = 0
            new_documents = 0

            if not self._embed_model:
                return {
                    "success": False,
                    "message": "GEMINI_API_KEY not found for embeddings",
                }

            for doc in documents:
                source = doc.metadata.get("source", "unknown")
                content_hash = self._generate_content_hash(doc.text, source)

                existing_id = self._find_existing_document(content_hash)

                if existing_id:
                    duplicates_found += 1
                    vector_ids.append(existing_id)

                    try:
                        self.client.set_payload(
                            collection_name=self.collection_name,
                            payload={"timestamp": current_time},
                            points=[existing_id],
                        )
                    except Exception as e:
                        print(
                            f"Warning: Failed to update timestamp for {existing_id}: {e}"
                        )

                    continue

                new_documents += 1
                vector_id = doc.doc_id or str(uuid.uuid4())
                vector_ids.append(vector_id)

                if not hasattr(doc, "embedding") or doc.embedding is None:
                    try:
                        embedding = self._embed_model.get_text_embedding(doc.text)
                        doc.embedding = embedding
                    except Exception as e:
                        return {
                            "success": False,
                            "message": f"Error generating embedding: {str(e)}",
                        }

                points_to_insert.append(
                    models.PointStruct(
                        id=vector_id,
                        vector=doc.embedding,
                        payload={
                            **doc.metadata,
                            "timestamp": current_time,
                            "text": doc.text[:1000],
                            "content_hash": content_hash,
                        },
                    )
                )

            if points_to_insert:
                self.client.upsert(
                    collection_name=self.collection_name, points=points_to_insert
                )

            return {
                "success": True,
                "message": f"Successfully processed {len(documents)} documents",
                "new_documents": new_documents,
                "duplicates_found": duplicates_found,
                "count": len(vector_ids),
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
