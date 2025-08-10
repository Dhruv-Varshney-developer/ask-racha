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
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.readers.web import SimpleWebPageReader, SitemapReader

import requests
from bs4 import BeautifulSoup

from cache import CacheDB

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

        self.index = None
        self.query_engine = None
        self.documents = []
        self.cache_documents = os.getenv("CACHE_DOCUMENTS", "false").lower() in ("true", "1", "yes")

        if self.cache_documents:
            print("🔍 Using cache")
            self.cache_db = CacheDB()


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
            # use cached content if it exists
            if self.cache_db:
                cached = self.cache_db.get_content(url)
                if cached:
                    print(f"using cached content for {url}")
                    return cached

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

            # add to cache if initialized
            if self.cache_db:
                self.cache_db.add(url, cleaned_text)

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
        
    def load_documents_from_cache(self):
        if self.cache_db:
            docs = self.cache_db.load_documents()
            if docs:
                self.index = VectorStoreIndex.from_documents(docs, show_progress=True)
                self.query_engine = self.index.as_query_engine(
                    similarity_top_k=6,
                    response_mode="tree_summarize",
                    verbose=True
                )
                self.documents = docs
                print(f"loaded {len(docs)} documents from cache")

                # Track cached URLs to avoid re-scraping
                self.cached_urls = set()
                for doc in docs:
                    source_url = doc.metadata.get('source')
                    if source_url:
                        self.cached_urls.add(source_url)
            else:
                self.cached_urls = set()
        else:
            self.cached_urls = set()


    def load_comprehensive_documentation(self, urls: List[str]) -> Dict:
        """Load comprehensive documentation using multiple discovery methods"""
        try:
            # first load all cached documents
            self.load_documents_from_cache()
            
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

            # Create vector index with enhanced configuration
            print(
                f"🧠 Creating comprehensive knowledge index from {len(all_documents)} documents...")
            self.index = VectorStoreIndex.from_documents(
                all_documents,
                show_progress=True
            )

            # Create advanced query engine
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=6,  # Retrieve more relevant chunks
                response_mode="tree_summarize",  # Better synthesis for comprehensive responses
                verbose=True
            )

            self.documents = (self.documents or []) + all_documents

            return {
                'success': True,
                'message': f'Successfully loaded comprehensive documentation: {len(all_documents)} pages',
                'loaded_urls': all_loaded_urls,
                'failed_urls': all_failed_urls,
                'document_count': len(all_documents),
                'total_chars': sum(len(doc.text) for doc in all_documents)
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
            # Skip if URL is already cached and loaded
            if hasattr(self, "cached_urls") and url in self.cached_urls:
                print(f"⚡ Skipping already cached URL: {url}")
                continue

            try:
                content = self.scrape_url_advanced(url)

                if content and len(content) > 200:
                    title = self.extract_content_title(content)
                    doc = Document(
                        text=content,
                        metadata={
                            'source': url,
                            'title': title,
                            'length': len(content),
                            'type': 'documentation_page'
                        }
                    )
                    documents.append(doc)
                    loaded_urls.append(url)

                    if self.cache_db:
                        self.cache_db.save_document(url, content, title, len(content))

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
