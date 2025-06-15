import os
import asyncio
from typing import List, Dict
from dotenv import load_dotenv

# Latest Google GenAI package (replaces google-generativeai)
from google import genai

# Latest LlamaIndex imports
from llama_index.core import (
    VectorStoreIndex, 
    Document, 
    Settings,
    StorageContext
)
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.readers.web import SimpleWebPageReader

import requests
from bs4 import BeautifulSoup

load_dotenv()

class AskRachaRAG:
    def __init__(self):
        # Get Gemini API key
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Configure Google GenAI client (new unified SDK)
        self.genai_client = genai.Client(api_key=self.gemini_api_key)
        
        # Configure LlamaIndex with latest Gemini integrations
        Settings.llm = Gemini(
            model="models/gemini-2.0-flash",  # Latest model
            api_key=self.gemini_api_key,
            temperature=0.1
        )
        
        Settings.embed_model = GeminiEmbedding(
            model_name="models/text-embedding-004",  # Latest embedding model
            api_key=self.gemini_api_key
        )
        
        self.index = None
        self.query_engine = None
        self.documents = []
    
    def scrape_url_advanced(self, url: str) -> str:
        """Advanced web scraping with BeautifulSoup"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
                element.decompose()
            
            # Try to find main content areas
            main_selectors = [
                'main',
                'article', 
                '[role="main"]',
                '.content',
                '.main-content',
                '.post-content',
                '.entry-content',
                '#content',
                '#main'
            ]
            
            main_content = None
            for selector in main_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            # Fallback to body if no main content found
            if not main_content:
                main_content = soup.body or soup
            
            # Extract text with better formatting
            text = main_content.get_text(separator='\n', strip=True)
            
            # Clean up text
            lines = []
            for line in text.split('\n'):
                line = line.strip()
                if len(line) > 3 and not line.startswith('http'):  # Filter out URLs and short lines
                    lines.append(line)
            
            cleaned_text = '\n'.join(lines)
            
            # Limit size but keep reasonable length
            return cleaned_text[:15000]
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return ""
    
    async def load_documents_async(self, urls: List[str]) -> Dict:
        """Load and index documents asynchronously"""
        try:
            documents = []
            loaded_urls = []
            failed_urls = []
            
            print(f"🔄 Loading {len(urls)} documents...")
            
            for url in urls:
                print(f"📄 Processing: {url}")
                content = self.scrape_url_advanced(url)
                
                if content and len(content) > 200:  # Minimum content threshold
                    # Extract title from content (first meaningful line)
                    title_lines = content.split('\n')[:5]
                    title = None
                    for line in title_lines:
                        if len(line) > 10 and len(line) < 100:
                            title = line
                            break
                    title = title or f"Document from {url}"
                    
                    doc = Document(
                        text=content,
                        metadata={
                            'source': url,
                            'title': title,
                            'length': len(content),
                            'type': 'web_page'
                        }
                    )
                    documents.append(doc)
                    loaded_urls.append(url)
                    print(f"✅ Loaded: {len(content)} characters - {title[:50]}...")
                else:
                    failed_urls.append(url)
                    print(f"❌ Failed to load meaningful content from: {url}")
            
            if not documents:
                return {
                    'success': False,
                    'message': 'No documents could be loaded with sufficient content',
                    'loaded_urls': [],
                    'failed_urls': failed_urls
                }
            
            # Create vector index with better configuration
            print("🧠 Creating vector index...")
            self.index = VectorStoreIndex.from_documents(
                documents,
                show_progress=True
            )
            
            # Create query engine with enhanced retrieval
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=4,  # Get more relevant chunks
                response_mode="tree_summarize",  # Better for longer contexts
                verbose=True
            )
            
            self.documents = documents
            
            return {
                'success': True,
                'message': f'Successfully loaded {len(documents)} documents',
                'loaded_urls': loaded_urls,
                'failed_urls': failed_urls,
                'document_count': len(documents),
                'total_chars': sum(len(doc.text) for doc in documents)
            }
            
        except Exception as e:
            print(f"Error in load_documents_async: {e}")
            return {
                'success': False,
                'message': f'Error loading documents: {str(e)}',
                'loaded_urls': [],
                'failed_urls': urls
            }
    
    def load_documents(self, urls: List[str]) -> Dict:
        """Synchronous wrapper for loading documents"""
        return asyncio.run(self.load_documents_async(urls))
    
    def query(self, question: str) -> Dict:
        """Query the RAG system with enhanced prompting"""
        try:
            if not self.query_engine:
                return {
                    'success': False,
                    'answer': 'No documents loaded. Please load documents first.',
                    'sources': []
                }
            
            print(f"🤔 Processing query: {question}")
            
            # Enhanced prompt for better Storacha-specific responses
            enhanced_question = f"""
            You are an expert assistant specialized in Storacha documentation.
            
            Please answer the following question based on the provided Storacha documentation.
            Be comprehensive, accurate, and helpful. Include specific details from the documentation.
            If you mention features or concepts, explain them clearly.
            If the question cannot be fully answered from the documentation, say so explicitly.
            
            User Question: {question}
            
            Please provide a detailed and helpful response:
            """
            
            response = self.query_engine.query(enhanced_question)
            
            # Extract sources with better metadata
            sources = []
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    if hasattr(node, 'metadata'):
                        source_info = {
                            'url': node.metadata.get('source', 'Unknown'),
                            'title': node.metadata.get('title', 'Document'),
                            'score': getattr(node, 'score', 0.0),
                            'snippet': node.text[:150] + "..." if hasattr(node, 'text') else ""
                        }
                        sources.append(source_info)
            
            return {
                'success': True,
                'answer': str(response),
                'sources': sources,
                'question': question,
                'model_used': 'gemini-2.0-flash'
            }
            
        except Exception as e:
            print(f"Error in query: {e}")
            return {
                'success': False,
                'answer': f'Sorry, I encountered an error processing your question: {str(e)}',
                'sources': [],
                'question': question
            }
    
    def get_status(self) -> Dict:
        """Get current system status with detailed info"""
        total_chars = sum(len(doc.text) for doc in self.documents) if self.documents else 0
        
        return {
            'documents_loaded': len(self.documents),
            'total_characters': total_chars,
            'index_ready': self.index is not None,
            'query_engine_ready': self.query_engine is not None,
            'model_info': {
                'llm': 'Gemini 2.0 Flash',
                'embeddings': 'Text Embedding 004',
                'framework': 'LlamaIndex 0.12.x'
            },
            'document_sources': [doc.metadata.get('source', 'Unknown') for doc in self.documents] if self.documents else []
        }
    
    def test_connection(self) -> Dict:
        """Test the Gemini API connection"""
        try:
            # Simple test query using the unified SDK
            response = self.genai_client.models.generate_content(
                model='gemini-2.0-flash',
                contents='Hello! Please respond with "Connection successful"'
            )
            
            return {
                'success': True,
                'message': 'Gemini API connection successful',
                'response': response.text
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Gemini API connection failed: {str(e)}'
            }