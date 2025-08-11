import os
import logging
import asyncio
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from pinecone.exceptions import PineconeApiException
import requests
from bs4 import BeautifulSoup

from neo4j import GraphDatabase

from llama_index.core import (
    VectorStoreIndex,
    Document,
    load_index_from_storage,
    Settings,
    StorageContext,
)

from llama_index.llms.gemini import Gemini
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.readers.web import SimpleWebPageReader, SitemapReader

load_dotenv()

URI = os.getenv('NEO4J_URI')
PASSWORD = os.getenv('NEO4J_PASSWORD')
USER = os.getenv('NEO4J_USER')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# -------------------- Knowledge Graph Using Neo4j --------------------
class Neo4jKnowledgeGraph:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def build_from_documents(self, documents: List[Document], extract_entities_fn):
        """
        Rebuilds the entire graph in Neo4j. Clears existing nodes.
        """
        with self.driver.session() as session:
            # Delete all existing nodes and relationships
            session.run("MATCH (n) DETACH DELETE n")
            # Create nodes and relationships
            for doc in documents:
                doc_id = doc.metadata['source']
                # Create or merge Doc node
                session.run(
                    "MERGE (d:Doc {id: $id})", {'id': doc_id}
                )
                entities = extract_entities_fn(doc.text)
                for entity in entities:
                    # Create or merge Entity node
                    session.run(
                        "MERGE (e:Entity {name: $name})", {'name': entity}
                    )
                    # Create relationship
                    session.run(
                        "MATCH (d:Doc {id: $id}), (e:Entity {name: $name}) \
                         MERGE (e)-[:REFERS_TO]->(d)",
                        {'id': doc_id, 'name': entity}
                    )

    def query_subgraph(self, query_entities: List[str], depth: int = 2) -> List[str]:
        """
        Returns document IDs within `depth` hops of listed entities.
        """
        if not query_entities:
            return []
        cypher = f"""
        UNWIND $entities AS ent
        MATCH (e:Entity {{name: ent}})-[:REFERS_TO*1..{depth}]-(d:Doc)
        RETURN DISTINCT d.id AS id
        """
        with self.driver.session() as session:
            result = session.run(cypher, entities=query_entities)
            return [record['id'] for record in result]

# -------------------- Main RAG Class --------------------
class AskRachaRAG:
    def __init__(
        self,
        pinecone_api_key: Optional[str] = None,
        pinecone_env: Optional[str] = None,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None,
        index_name: str = 'askrachadb',
        kg_extract_fn=None
    ):
        # Load API keys & connection info
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        pinecone_api_key = pinecone_api_key or os.getenv('PINECONE_API_KEY')
        neo4j_uri = neo4j_uri or os.getenv('NEO4J_URI')
        neo4j_user = neo4j_user or os.getenv('NEO4J_USER')
        neo4j_password = neo4j_password or os.getenv('NEO4J_PASSWORD')
        if not all([self.gemini_api_key, pinecone_api_key, neo4j_uri, neo4j_user, neo4j_password]):
            raise ValueError('Missing GEMINI_API_KEY, PINECONE_API_KEY, or NEO4J_URI/USER/PASSWORD')

        # Configure LLM + Embeddings
        Settings.llm = Gemini(model='models/gemini-2.0-flash', api_key=self.gemini_api_key, temperature=0.1)
        Settings.embed_model = GoogleGenAIEmbedding(model_name='models/text-embedding-004', api_key=self.gemini_api_key)


        self.genai_client = GoogleGenAI(model='models/gemini-2.0-flash', api_key=self.gemini_api_key, temperature=0.1)

        # 1. Initialize Pinecone
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        try:
            if index_name not in pc.list_indexes():
                pc.create_index(
                    name=index_name,
                    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                    metric="cosine",
                    dimension=768,
                )
        except PineconeApiException as e:
            if e.status != 409:
                raise

        # 2. Rehydrate storage context
        pinecone_client = pc.Index(index_name)
        print(f"Pinecone client = {pinecone_client}")
        self.pinecone_index = pinecone_client
        pinecone_store = PineconeVectorStore(
            client=self.pinecone_index,
            index_name=index_name,
            text_key='text',
        )
        print(f"Pinecone store = {pinecone_store}")
        self.storage_context = StorageContext.from_defaults(vector_store=pinecone_store)
        print(f"Storage context = {self.storage_context}")

        # 3. Attempt to load existing index
        try:
            self.index = VectorStoreIndex.from_vector_store(
                vector_store=pinecone_store,
            )   
            print("✅ Index loaded successfully")
        except Exception:
            self.index = None
            print("❌ Index not found")

        # 4. Wire up query engine only if index is ready
        if self.index:
            print("✅ Query engine prepared successfully")
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=10,
                response_mode="tree_summarize",
                verbose=False,
            )
        else:
            self.query_engine = None

        # 5. Configure chunking for future builds (if you ever need to ingest new docs)
        Settings.chunk_size = 768
        Settings.chunk_overlap = 64

        # 6. Knowledge Graph setup
        self.kg = Neo4jKnowledgeGraph(neo4j_uri, neo4j_user, neo4j_password)
        self.extract_entities_fn = kg_extract_fn or (lambda text: [])
        self.documents: List[Document] = []

    def extract_content_title(self, content: str) -> str:
        """Extract meaningful title from document content"""
        lines = content.split('\n')[:10]
        for line in lines:
            line = line.strip()
            if 10 <= len(line) <= 100 and not line.startswith('http'):
                return line
        return "Documentation Page"

    
    # -------------------- Web Scraping --------------------
    def scrape_url(self, url: str) -> str:
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
            return ""


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

    def discover_urls(self, base_url: str) -> List[str]:
        """Discover documentation URLs by analyzing page structure"""
        discovered_urls = set()

        try:
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
            return urls_list

        except Exception as e:
            print(f"❌ URL discovery failed: {e}")
            return [base_url]

    def process_url_batch(self, urls: List[str]) -> tuple:
        """Process a batch of URLs and return documents, loaded URLs, and failed URLs"""
        documents = []
        loaded_urls = []
        failed_urls = []

        for url in urls:
            try:
                content = self.scrape_url(url)

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

    # -------------------- Build Index --------------------
    def build_index_from_urls(self, urls: List[str]) -> Dict:
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
                    discovered_urls = self.discover_urls(
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
                        content = self.scrape_url(base_url)
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
            self.documents = all_documents

            # Vector index
            self.index = VectorStoreIndex.from_documents(
                all_documents,
                storage_context=self.storage_context,
                show_progress=True
            )

            # Build KG in Neo4j
            self.kg.build_from_documents(all_documents, self.extract_entities_fn)

            # Prepare query engine
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=10,
                response_mode='tree_summarize',
                verbose=False
            )

            return {
                'success': True,
                'message': 'Documentation loaded successfully',
                'loaded_urls': all_loaded_urls,
                'failed_urls': all_failed_urls,
                'loaded': len(all_documents)
            }
        except Exception as e:
            print(f"Error in comprehensive documentation loading: {e}")
            return {
                'success': False,
                'message': f'Error loading comprehensive documentation: {str(e)}',
                'loaded_urls': [],
                'failed_urls': urls
            }

    # -------------------- Hybrid Retrieval --------------------
    async def _hybrid_retrieve(self, query: str) -> List[Document]:
        entities = self.extract_entities_fn(query)
        seed_sources = self.kg.query_subgraph(entities, depth=2)
        q_emb = await Settings.embed_model.aget_query_embedding(query)
        if seed_sources:
            filter_meta = {'source': {'$in': seed_sources}}
            res = self.pinecone_index.query(
                vector=q_emb,
                top_k=10,
                filter=filter_meta,
                include_metadata=True
            )
        else:
            res = self.pinecone_index.query(vector=q_emb, top_k=10, include_metadata=True)
        docs = [Document(text=m['metadata'].get('text',''), metadata=m['metadata']) for m in res['matches']]
        return docs

    # -------------------- Query Interface --------------------
    async def query(self, question: str) -> Dict:
        if not self.index:
            return {
                'success': False, 
                'answer': 'Index not initialized or query engine not prepared.',
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

        # 1) Embed + retrieve raw Pinecone matches so we can grab score, metadata, etc.
        q_emb = await Settings.embed_model.aget_query_embedding(question)
        pinecone_resp = self.pinecone_index.query(
            vector=q_emb,
            top_k=10,
            include_metadata=True
        )

        # 2) Turn those into {url, title, score} dicts
        sources = []
        for match in pinecone_resp['matches']:
            md    = match['metadata']
            url   = md.get('source', '')
            title = md.get('title', url)
            score = float(match.get('score', 0.0))
            sources.append({
                'url':   url,
                'title': title,
                'score': score,
            })
        response = self.query_engine.query(enhanced_question)
        return {
            'success': True,
            'answer': str(response),
            'question': question,
            'sources': sources,
            'model_used': 'gemini-2.0-flash'
        }

    def query_sync(self, question: str) -> Dict:
        return asyncio.run(self.query(question))


    def get_status(self) -> Dict:
        """
        Get current system status with comprehensive information.
        All fields are guaranteed to be JSON‐serializable primitives.
        """
        try:
            # 1. In-memory document metrics
            docs_loaded     = len(self.documents)
            total_characters = sum(len(doc.text) for doc in self.documents)

            # 2. Vector DB metrics (if index is ready)
            vec_stats = {}
            if getattr(self, 'pinecone_index', None) and self.index:
                describe = getattr(self.pinecone_index, 'describe_index_stats', None)
                if callable(describe):
                    raw = describe()
                    # Convert NamespaceSummary objects into plain dicts
                    namespaces = {}
                    for name, summary in raw.get('namespaces', {}).items():
                        namespaces[name] = {
                            'vector_count': getattr(summary, 'vector_count', None),
                            'segment_count': getattr(summary, 'segment_count', None)
                        }
                    vec_stats = {
                        'total_vectors': raw.get('total_vector_count', 0),
                        'namespaces': namespaces
                    }

            # 3. Build the clean payload
            return {
                'success': True,
                'initialized': True,
                'message': 'System status retrieved successfully',
                'documents_loaded': docs_loaded,
                'total_characters': total_characters,
                'index_ready': bool(self.index),
                'query_engine_ready': bool(self.query_engine),
                'vector_db': vec_stats,
                'vector_count': vec_stats.get('total_vectors', 0),
                'model_info': {
                    'llm': 'Gemini 2.0 Flash',
                    'embeddings': 'Text Embedding 004',
                    'framework': 'LlamaIndex 0.12.x'
                }
            }
        except Exception as e:
            return {
                'success': False,
                'initialized': False,
                'message': f'Status connection failed: {e}'
            }

    def test_connection(self) -> Dict:
        """Test the Gemini API connection"""
        try:
            # Use the .complete() method for a simple request
            response = self.genai_client.complete(
                'Hello! Please respond with "Connection successful"'
            )

            # The response object itself is a string-like object
            return {
                'success': True,
                'message': 'Gemini API connection successful',
                'response': str(response)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Gemini API connection failed: {str(e)}'
            }

# -------------------- Example Usage --------------------
if __name__ == '__main__':
    rag = AskRachaRAG(
        kg_extract_fn=lambda txt: txt.split()[:100]
    )
    # print(rag.build_index_from_urls(['https://docs.storacha.network']))
    # print(rag.query_sync('How do I get started with storacha?'))
    print(rag.get_status())
    print(rag.test_connection())