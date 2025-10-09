import os
import asyncio
from typing import List, Dict
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv

from google import genai

# Latest LlamaIndex imports
from llama_index.core import (
    VectorStoreIndex,
    Document,
    Settings,
    StorageContext
)

from llama_index.core.indices.loading import load_index_from_storage
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.readers.web import SimpleWebPageReader, SitemapReader

import requests
from bs4 import BeautifulSoup

from storage.vector_store import VectorStore
from cleaning.processors import RepoProcessor

load_dotenv()


class AskRachaRAG:
    def __init__(self):
        # Get Gemini API key
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in environment variables")

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

        self.vector_store = VectorStore(is_local=True)

        self.index = None
        self.query_engine = None
        self.documents = []
        self.documents_already_embedded = False  # Flag to track if docs have embeddings

        self._initialize_vector_store()

    def _initialize_vector_store(self):
        """Initialize the vector store and load existing documents if any"""
        try:
            init_result = self.vector_store.initialize_index()
            if not init_result["success"]:
                print(
                    f"Warning: Vector store initialization failed: {init_result['message']}"
                )
                return

            stats = self.vector_store.get_stats()
            if stats["success"] and stats["stats"].points_count > 0:
                print(
                    f"Found {stats['stats'].points_count} existing documents in vector store"
                )
                self._load_existing_documents()
        except Exception as e:
            print(f"Warning: Error initializing vector store: {e}")
            
    def _process_github_repos(self):
        """Process GitHub repositories and add them to the vector store"""
        try:
            processor = RepoProcessor()
            repo_docs = processor.process_repos()
            
            if repo_docs:
                print(f"Found {len(repo_docs)} documents in GitHub repos")
                
                result = self.vector_store.upsert_documents(repo_docs)
                if not result["success"]:
                    raise Exception(f"Failed to store repo documents: {result['message']}")
                
                self.documents += repo_docs
                    
                print("Successfully processed and stored GitHub repo documents")
            else:
                print("No documents found in GitHub repos")
                
        except Exception as e:
            print(f"Error processing GitHub repos: {e}")

    def _load_existing_documents(self):
        """Load existing documents from vector store into memory and load existing index"""
        try:
            print("Loading existing documents from vector store...")
            
            all_points = self.vector_store.client.scroll(
                collection_name=self.vector_store.collection_name,
                limit=1000,
                with_payload=True
            )[0]
            
            if all_points:
                print(f"Found {len(all_points)} points in vector store")

                for point in all_points:
                    if hasattr(point, 'payload') and point.payload:
                        text = point.payload.get('text', '')
                        
                        metadata = {}
                        if 'source' in point.payload:
                            metadata['source'] = point.payload['source']
                        if 'title' in point.payload:
                            metadata['title'] = point.payload['title']
                        if 'type' in point.payload:
                            metadata['type'] = point.payload['type']
                        if 'length' in point.payload:
                            metadata['length'] = point.payload['length']
                        
                        doc = Document(text=text, metadata=metadata)
                        self.documents.append(doc)
                
                print(f"Loaded {len(self.documents)} documents into memory")
                
                if self.documents:
                    self._create_lightweight_index()
            else:
                print("No documents found in vector store")
                
        except Exception as e:
            print(f"Error loading existing documents: {e}")

    def _build_index(self):
        """Build LlamaIndex from loaded documents"""
        try:
            print(f"Building knowledge index from {len(self.documents)} documents...")
            self.index = VectorStoreIndex.from_documents(
                self.documents,
                show_progress=True
            )

            self.query_engine = self.index.as_query_engine(
                similarity_top_k=6,
                response_mode="tree_summarize",
                verbose=True
            )
            print("Index and query engine built successfully")
            
            self._save_persistent_index()
            
        except Exception as e:
            print(f"Error building index: {e}")
    
    def _create_lightweight_index(self):
        """Create a lightweight index without regenerating embeddings"""
        try:
            print("Creating lightweight index from existing documents...")
            
            if self._load_persistent_index():
                print("Persistent index loaded successfully (no embedding regeneration)")
                return
            
            print("Creating minimal index for existing documents...(might take a minute )")
            self.index = VectorStoreIndex.from_documents(
                self.documents,
                show_progress=False,
                embed_metadata=False
            )
            
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=6,
                response_mode="tree_summarize",
                verbose=True
            )
            
            self._save_persistent_index()
            
            print("Lightweight index created and saved for future use")
            
        except Exception as e:
            print(f"Error creating lightweight index: {e}")
            print("Falling back to full index rebuild...")
            self._build_index()

    def _save_persistent_index(self):
        """Save the current index to disk for future loading"""
        try:
            index_dir = "persistent_index"
            if not os.path.exists(index_dir):
                os.makedirs(index_dir)
            
            self.index.storage_context.persist(persist_dir=index_dir)
            print(f"Index saved to {index_dir}")
        except Exception as e:
            print(f"Warning: Could not save persistent index: {e}")
    
    def _load_persistent_index(self):
        """Load existing index from disk if available"""
        try:
            index_dir = "persistent_index"
            
            if not os.path.exists(index_dir):
                return False
            
            if not os.path.exists(os.path.join(index_dir, "docstore.json")):
                return False
            
            print(f"Loading persistent index from {index_dir}...")
            
            storage_context = StorageContext.from_defaults(persist_dir=index_dir)
            self.index = load_index_from_storage(storage_context)
            
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=6,
                response_mode="tree_summarize",
                verbose=True
            )
            
            return True
            
        except Exception as e:
            print(f"Warning: Could not load persistent index: {e}")
            return False

    def extract_content_title(self, content: str) -> str:
        """Extract meaningful title from document content"""
        lines = content.split('\n')[:10]
        for line in lines:
            line = line.strip()
            if 10 <= len(line) <= 100 and not line.startswith('http'):
                return line
        return "Documentation Page"

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

    def discover_documentation_urls(self, base_url: str) -> List[str]:
        """Discover documentation URLs by analyzing page structure"""
        discovered_urls = set()

        try:
            print(f"🔍 Analyzing page structure for: {base_url}")
            response = requests.get(base_url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all internal links
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_url, href)

                # Filter for same domain only
                if urlparse(full_url).netloc == urlparse(base_url).netloc:
                    # Look for documentation-related patterns
                    url_lower = full_url.lower()
                    if any(pattern in url_lower for pattern in [
                        'docs', 'guide', 'tutorial', 'help', 'api', 'reference',
                        'quickstart', 'getting-started', 'concept', 'how-to',
                        'overview', 'intro', 'setup', 'install', 'config',
                        'examples', 'learn', 'manual', 'handbook'
                    ]):
                        discovered_urls.add(full_url)

            # Limit results to prevent overload
            urls_list = list(discovered_urls)[:100]
            print(f"✅ Discovered {len(urls_list)} documentation pages")
            return urls_list

        except Exception as e:
            print(f"❌ URL discovery failed: {e}")
            return [base_url]

    def load_comprehensive_documentation(self, urls: List[str]) -> Dict:
        """Load comprehensive documentation using multiple discovery methods"""
        try:
            all_documents = []
            all_loaded_urls = []
            all_failed_urls = []

            print(
                f"🔄 Loading comprehensive documentation from {len(urls)} sources...")

            for base_url in urls:
                print(f"📚 Processing documentation source: {base_url}")

                # Method 1: Try structured content discovery
                structured_urls = self.discover_structured_content(base_url)

                if len(structured_urls) > 1:
                    print(f"✅ Found {len(structured_urls)} structured pages")
                    documents, loaded, failed = self.process_url_batch(
                        structured_urls[:50])
                    all_documents.extend(documents)
                    all_loaded_urls.extend(loaded)
                    all_failed_urls.extend(failed)
                else:
                    # Method 2: Manual URL discovery
                    print("🔍 Using manual discovery method")
                    discovered_urls = self.discover_documentation_urls(
                        base_url)

                    if len(discovered_urls) > 1:
                        documents, loaded, failed = self.process_url_batch(
                            discovered_urls[:50])
                        all_documents.extend(documents)
                        all_loaded_urls.extend(loaded)
                        all_failed_urls.extend(failed)
                    else:
                        # Method 3: Single page fallback
                        print("📄 Loading single page")
                        content = self.scrape_url_advanced(base_url)
                        if content and len(content) > 200:
                            doc = Document(
                                text=content,
                                metadata={
                                    'source': base_url,
                                    'title': self.extract_content_title(content),
                                    'length': len(content),
                                    'type': 'documentation_page'
                                }
                            )
                            all_documents.append(doc)
                            all_loaded_urls.append(base_url)
                        else:
                            all_failed_urls.append(base_url)

            if not all_documents:
                return {
                    'success': False,
                    'message': 'No documentation content could be loaded',
                    'loaded_urls': [],
                    'failed_urls': all_failed_urls
                }

            print(
                f"💾 Storing {len(all_documents)} documents in persistent vector store..."
            )
            vector_result = self.vector_store.upsert_documents(all_documents)

            if not vector_result["success"]:
                return {
                    "success": False,
                    "message": f'Error storing documents in vector store: {vector_result["message"]}',
                    "loaded_urls": [],
                    "failed_urls": urls,
                }


            self.documents += all_documents

            return {
                'success': True,
                'message': f'Successfully loaded comprehensive documentation: {len(all_documents)} pages',
                'loaded_urls': all_loaded_urls,
                'failed_urls': all_failed_urls,
                'document_count': len(all_documents),
                'total_chars': sum(len(doc.text) for doc in all_documents),
                "vector_store_ids": vector_result.get("ids", []),
            }

        except Exception as e:
            print(f"Error in comprehensive documentation loading: {e}")
            return {
                'success': False,
                'message': f'Error loading comprehensive documentation: {str(e)}',
                'loaded_urls': [],
                'failed_urls': urls
            }

    def discover_structured_content(self, base_url: str) -> List[str]:
        """Discover structured content using standard web discovery methods"""
        discovered_urls = []

        # Common structured content locations
        structured_endpoints = [
            f"{base_url.rstrip('/')}/sitemap.xml",
            f"{base_url.rstrip('/')}/sitemap_index.xml",
            f"{base_url.rstrip('/')}/sitemap-index.xml"
        ]

        for endpoint in structured_endpoints:
            try:
                print(f"🔍 Checking structured content at: {endpoint}")

                # Use specialized reader for structured content
                content_reader = SitemapReader()
                documents = content_reader.load_data(sitemap_url=endpoint)

                if documents:
                    urls = []
                    for doc in documents:
                        source_url = doc.metadata.get(
                            'loc') or doc.metadata.get('source', endpoint)
                        if source_url:
                            urls.append(source_url)

                    if urls:
                        print(f"✅ Found {len(urls)} structured content pages")
                        return urls

            except Exception as e:
                print(
                    f"⚠️ Structured content discovery failed for {endpoint}: {str(e)}")
                continue

        return discovered_urls

    def process_url_batch(self, urls: List[str]) -> tuple:
        """Process a batch of URLs and return documents, loaded URLs, and failed URLs"""
        documents = []
        loaded_urls = []
        failed_urls = []

        for url in urls:
            try:
                content = self.scrape_url_advanced(url)

                if content and len(content) > 200:
                    doc = Document(
                        text=content,
                        metadata={
                            'source': url,
                            'title': self.extract_content_title(content),
                            'length': len(content),
                            'type': 'documentation_page'
                        }
                    )
                    documents.append(doc)
                    loaded_urls.append(url)
                    print(f"✅ Loaded: {len(content)} chars from {url}")
                else:
                    failed_urls.append(url)
                    print(f"❌ Insufficient content from: {url}")

            except Exception as e:
                failed_urls.append(url)
                print(f"❌ Failed to load {url}: {str(e)}")

        return documents, loaded_urls, failed_urls

    async def load_documents_async(self, urls: List[str]) -> Dict:
        """Load comprehensive documentation asynchronously"""
        return self.load_comprehensive_documentation(urls)

    def load_documents(self, urls: List[str]) -> Dict:
        """Synchronous wrapper for comprehensive documentation loading"""
        return asyncio.run(self.load_documents_async(urls))

    def query(self, question: str) -> Dict:
        """Query the comprehensive knowledge system with enhanced prompting"""
        try:
            if not self.query_engine:
                return {
                    'success': False,
                    'answer': 'No documentation loaded. Please load the knowledge base first.',
                    'sources': []
                }

            print(f"🤔 Processing query: {question}")

            # Enhanced prompt for comprehensive responses
            enhanced_question = f"""
            You are an expert assistant with comprehensive knowledge of the loaded documentation.
            
            Please answer the following question based on the provided documentation.
            Be thorough, accurate, and helpful. Include specific details and examples where available.
            If you reference features or concepts, explain them clearly for better understanding.
            If the question cannot be fully answered from the available documentation, clearly indicate this.
            
            User Question: {question}
            
            Please provide a comprehensive and helpful response:
            """

            response = self.query_engine.query(enhanced_question)

            # Extract sources with enhanced metadata
            sources = []
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    if hasattr(node, 'metadata'):
                        source_info = {
                            'url': node.metadata.get('source', 'Unknown'),
                            'title': node.metadata.get('title', 'Documentation Page'),
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
            print(f"Error in query processing: {e}")
            return {
                'success': False,
                'answer': f'Sorry, I encountered an error processing your question: {str(e)}',
                'sources': [],
                'question': question
            }

    def get_status(self) -> Dict:
        """Get current system status with comprehensive information"""
        total_chars = sum(len(doc.text)
                          for doc in self.documents) if self.documents else 0

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

    def query_with_context(self, query: str, context: List[Dict]) -> Dict:
        """
        Generate a response considering the conversation context
        """
        try:
            conversation_context = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in context
            ])
            
            enhanced_prompt = f"""Previous conversation:
{conversation_context}

Current question: {query}

Analyze the context and question, then provide:
1. A decision on whether sources should be shown (true/false) based on:
   - If the response references technical information
   - If sources were actually used to generate the response
   - If the response builds on or clarifies previous technical information
   - Don't show sources for simple acknowledgments unless they relate to technical content

2. A response that:
   - Is consistent with the previous conversation
   - Answers the question directly
   - Uses simple language for basic questions
   - Provides detailed technical information only when necessary

Format your response as:
<show_sources>true/false</show_sources>
<response>Your actual response here</response>
"""
            
            response = self.query_engine.query(enhanced_prompt)
            response_text = str(response)
            
            response_text = str(response)
            
            show_sources = True  
            if '<show_sources>' in response_text and '</show_sources>' in response_text:
                show_sources_text = response_text.split('<show_sources>')[1].split('</show_sources>')[0].strip().lower()
                show_sources = show_sources_text == 'true'
                
            if '<response>' in response_text and '</response>' in response_text:
                response_text = response_text.split('<response>')[1].split('</response>')[0].strip()
                
            if not show_sources:
                return {
                    "success": True,
                    "response": response_text,
                    "source_nodes": []
                }

            source_nodes = []
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    if hasattr(node, 'score') and float(node.score) > 0.5:
                        source = {
                            'url': node.metadata.get('source', '') if hasattr(node, 'metadata') else '',
                            'title': node.metadata.get('title', 'Documentation') if hasattr(node, 'metadata') else 'Documentation',
                            'score': float(node.score)
                        }
                        if source['url'] and source['title']:
                            source_nodes.append(source)

            result = {
                "success": True,
                "response": response_text,
                "source_nodes": source_nodes
            }
            print("DEBUG: Final response with sources:", result)
            return result
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error generating response: {str(e)}"
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
