import os
import time
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from llama_index.core import Document

CACHE_TTL_MINS = os.getenv("CACHE_DURATION", 60 * 3600)

class CacheDB:
  def __init__(self):
      # validate db env config 
      mongo_uri = os.getenv("MONGO_DB_URI")
      if not mongo_uri:
          raise ValueError(
              "MONGO_DB_URI not found in environment variables")

      mongo_db_name = os.getenv("MONGO_DB_NAME")
      if not mongo_db_name:
          raise ValueError(
              "MONGO_DB_NAME not found in environment variables")

      self.mongo_client = MongoClient(mongo_uri)

      try:
          self.mongo_client.admin.command('ping')
          print("CacheDB connected successfully")
      except PyMongoError as e:
          print("no connection")
          raise ConnectionError(f"Could not connect to cache store: {e}")
      
      self.db = self.mongo_client[mongo_db_name]
      self.cache_collection = self.db["url_cache"]
      self.documents_collection = self.db["documents"]

  def load_documents(self):
      docs = []
      for record in self.documents_collection.find():
          doc = Document(
            text=record.get("text", ""),
            metadata={
              "source": record.get("source", ""),
              "title": record.get("title", ""),
              "length": record.get("length", 0),
              "type": record.get("type", "documentation_page")
            }
          )
          docs.append(doc)
      return docs
  
  def save_document(self, source: str, text: str, title: str, length: int, doc_type="documentation_page"):
      self.documents_collection.update_one(
          {"source": source},
          {"$set": {
            "text": text,
            "title": title,
            "length": length,
            "type": doc_type,
            "last_updated": time.time()
          }},
          upsert=True
      )

  def add(self, url: str, content: str):
      self.cache_collection.update_one(
          {"url": url},
          {"$set": {"content": content, "cached_at": time.time()}},
          upsert=True
      )

  def get_content(self, url: str) -> str | None:
      record = self.cache_collection.find_one({"url": url})
      if record:
          cached_time = record.get("cached_at", 0)
          if time.time() - cached_time < CACHE_TTL_MINS:
              return record.get("content")
      return None
