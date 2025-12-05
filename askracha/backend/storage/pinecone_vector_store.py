from typing import List, Dict, Optional
import os
import hashlib
from datetime import datetime
from pinecone import Pinecone, ServerlessSpec
from llama_index.core import Document
from llama_index.embeddings.gemini import GeminiEmbedding
import uuid
import time


class PineconeVectorStore:
    """Vector database interface for storing and querying document embeddings using Pinecone."""

    def __init__(self):
        """Initialize Pinecone vector store with API key and environment."""
        self.api_key = os.getenv("PINECONE_API_KEY")
        if not self.api_key:
            raise ValueError("PINECONE_API_KEY not found in environment variables")

        # Initialize Pinecone client
        self.pc = Pinecone(api_key=self.api_key)
        
        # Index configuration
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "askracha-docs")
        self.dimension = 768  # Gemini text-embedding-004 dimension
        
        # Get Gemini API key for embeddings
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key:
            self._embed_model = GeminiEmbedding(
                model_name="models/text-embedding-004", 
                api_key=gemini_api_key
            )
        else:
            self._embed_model = None

        # Connect to or create index
        self._ensure_index_exists()
        self.index = self.pc.Index(self.index_name)

    def _ensure_index_exists(self):
        """Create Pinecone index if it doesn't exist."""
        try:
            existing_indexes = [idx.name for idx in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                print(f"Creating Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
                    )
                )
                # Wait for index to be ready
                while not self.pc.describe_index(self.index_name).status['ready']:
                    time.sleep(1)
                print(f"Pinecone index {self.index_name} created successfully")
            else:
                print(f"Pinecone index {self.index_name} already exists")
        except Exception as e:
            print(f"Error ensuring index exists: {e}")
            raise

    def _generate_content_hash(self, text: str, source: str) -> str:
        """Generate a unique hash for document content and source."""
        content = f"{source}:{text[:1000]}"  # Using first 1000 chars + source
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def _find_existing_document(self, content_hash: str) -> Optional[str]:
        """Find existing document by content hash using metadata filtering."""
        try:
            # Query with metadata filter
            results = self.index.query(
                vector=[0.0] * self.dimension,  # Dummy vector for metadata-only query
                filter={"content_hash": {"$eq": content_hash}},
                top_k=1,
                include_metadata=True
            )
            
            if results.matches and len(results.matches) > 0:
                return results.matches[0].id
            return None
        except Exception as e:
            print(f"Error finding existing document: {e}")
            return None

    def initialize_index(self) -> Dict:
        """Initialize/verify the Pinecone index."""
        try:
            self._ensure_index_exists()
            return {
                "success": True,
                "message": f"Pinecone index {self.index_name} is ready"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error initializing index: {str(e)}"
            }

    def upsert_documents(self, documents: List[Document]) -> Dict:
        """Insert or update documents with deduplication."""
        try:
            current_time = int(datetime.now().timestamp())
            vectors_to_upsert = []
            vector_ids = []
            duplicates_found = 0
            new_documents = 0

            if not self._embed_model:
                return {
                    "success": False,
                    "message": "GEMINI_API_KEY not found for embeddings"
                }

            for doc in documents:
                source = doc.metadata.get("source", "unknown")
                content_hash = self._generate_content_hash(doc.text, source)

                # Check for existing document
                existing_id = self._find_existing_document(content_hash)

                if existing_id:
                    duplicates_found += 1
                    vector_ids.append(existing_id)
                    
                    # Update timestamp for existing document
                    try:
                        self.index.update(
                            id=existing_id,
                            set_metadata={"timestamp": current_time}
                        )
                    except Exception as e:
                        print(f"Warning: Failed to update timestamp for {existing_id}: {e}")
                    
                    continue

                new_documents += 1
                vector_id = doc.doc_id or str(uuid.uuid4())
                vector_ids.append(vector_id)

                # Generate embedding if not present
                if not hasattr(doc, "embedding") or doc.embedding is None:
                    try:
                        embedding = self._embed_model.get_text_embedding(doc.text)
                        doc.embedding = embedding
                    except Exception as e:
                        return {
                            "success": False,
                            "message": f"Error generating embedding: {str(e)}"
                        }

                # Prepare metadata for Pinecone
                metadata = {
                    **doc.metadata,
                    "timestamp": current_time,
                    "text": doc.text[:1000],  # Store first 1000 chars in metadata
                    "content_hash": content_hash
                }

                vectors_to_upsert.append({
                    "id": vector_id,
                    "values": doc.embedding,
                    "metadata": metadata
                })

            # Batch upsert to Pinecone
            if vectors_to_upsert:
                # Pinecone recommends batches of 100
                batch_size = 100
                for i in range(0, len(vectors_to_upsert), batch_size):
                    batch = vectors_to_upsert[i:i + batch_size]
                    self.index.upsert(vectors=batch)
                    print(f"Upserted batch {i//batch_size + 1} ({len(batch)} vectors)")

            return {
                "success": True,
                "message": f"Successfully processed {len(documents)} documents",
                "new_documents": new_documents,
                "duplicates_found": duplicates_found,
                "count": len(vector_ids),
                "ids": vector_ids
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error upserting documents: {str(e)}"
            }

    def delete_documents(self, ids: List[str]) -> Dict:
        """Delete documents by their unique IDs."""
        try:
            self.index.delete(ids=ids)
            return {
                "success": True,
                "message": "Documents deleted successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error deleting documents: {str(e)}"
            }

    def cleanup_old_vectors(self, before_timestamp: int) -> Dict:
        """Delete vectors older than specified timestamp."""
        try:
            # Pinecone uses metadata filtering for deletion
            self.index.delete(
                filter={"timestamp": {"$lt": before_timestamp}}
            )
            return {
                "success": True,
                "message": f"Successfully cleaned up vectors before timestamp {before_timestamp}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error cleaning up vectors: {str(e)}"
            }

    def get_stats(self) -> Dict:
        """Get index statistics."""
        try:
            stats = self.index.describe_index_stats()
            
            return {
                "success": True,
                "stats": type(
                    "Stats",
                    (),
                    {
                        "vectors_count": stats.total_vector_count,
                        "points_count": stats.total_vector_count,
                        "segments_count": len(stats.namespaces) if hasattr(stats, 'namespaces') else 1,
                        "status": "ready"
                    }
                )()
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error getting stats: {str(e)}"
            }

    def get_all_vectors(self, limit: int = 1000) -> List[Dict]:
        """
        Retrieve all vectors from the index (for migration/inspection).
        Note: Pinecone doesn't have a direct 'scroll' like Qdrant, 
        so this uses query with a dummy vector.
        """
        try:
            # Query with dummy vector to get all results
            results = self.index.query(
                vector=[0.0] * self.dimension,
                top_k=limit,
                include_metadata=True
            )
            
            vectors = []
            for match in results.matches:
                vectors.append({
                    "id": match.id,
                    "metadata": match.metadata,
                    "score": match.score
                })
            
            return vectors
        except Exception as e:
            print(f"Error retrieving vectors: {e}")
            return []
